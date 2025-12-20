"""
Google Forms specific handler.

Specialized logic for detecting and filling Google Forms.
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from core.interfaces import FormField, FormFillerStrategy, ActionResult, ActionStatus
from core.events import Event, EventType, EventDispatcher


@dataclass
class GoogleFormQuestion:
    """Represents a question in a Google Form."""
    index: int
    title: str
    description: str
    field_type: str  # short_text, paragraph, radio, checkbox, dropdown, date, time
    required: bool
    options: List[str]
    selector: str
    filled: bool = False
    value: str = ""


class GoogleFormsFiller:
    """
    Specialized handler for Google Forms.
    
    Handles the unique structure and selectors of Google Forms.
    """
    
    def __init__(self, strategy: FormFillerStrategy):
        self.strategy = strategy
        self.dispatcher = EventDispatcher()
        self.questions: List[GoogleFormQuestion] = []
    
    async def detect_form(self, page: Any) -> bool:
        """Detect if the page is a Google Form."""
        try:
            # Check for Google Forms indicators
            is_google_form = await page.evaluate("""
                () => {
                    return document.querySelector('[data-params]') !== null ||
                           document.querySelector('.freebirdFormviewerViewHeaderHeader') !== null ||
                           window.location.href.includes('docs.google.com/forms') ||
                           window.location.href.includes('forms.gle');
                }
            """)
            
            if is_google_form:
                self.dispatcher.dispatch(Event(
                    event_type=EventType.FORM_DETECTED,
                    message="Google Form detected",
                    data={"url": page.url}
                ))
            
            return is_google_form
        except:
            return False
    
    async def extract_questions(self, page: Any) -> List[GoogleFormQuestion]:
        """Extract all questions from the Google Form."""
        
        js_code = """
        () => {
            const questions = [];
            
            // Find all question containers
            const questionContainers = document.querySelectorAll(
                '.Qr7Oae, ' +
                '.freebirdFormviewerComponentsQuestionBaseRoot, ' +
                '[data-params]'
            );
            
            questionContainers.forEach((container, idx) => {
                // Get question title
                const titleEl = container.querySelector(
                    '.M7eMe, ' +
                    '[role="heading"], ' +
                    '.freebirdFormviewerComponentsQuestionBaseTitle'
                );
                const title = titleEl ? titleEl.textContent.trim() : '';
                
                // Skip if no title (likely not a question)
                if (!title) return;
                
                // Get description if exists
                const descEl = container.querySelector('.gubaDc, .freebirdFormviewerComponentsQuestionBaseDescription');
                const description = descEl ? descEl.textContent.trim() : '';
                
                // Check if required
                const required = container.querySelector('[aria-label*="Required"]') !== null ||
                                container.querySelector('.vnumgf') !== null;
                
                // Determine field type and get options
                let fieldType = 'short_text';
                let options = [];
                let selector = '';
                
                // Check for text input (short answer)
                const shortInput = container.querySelector('input[type="text"], input:not([type])');
                if (shortInput) {
                    fieldType = 'short_text';
                    selector = `[data-params] input[type="text"]`;
                }
                
                // Check for paragraph (long answer)
                const textarea = container.querySelector('textarea');
                if (textarea) {
                    fieldType = 'paragraph';
                    selector = `textarea`;
                }
                
                // Check for radio buttons
                const radioGroup = container.querySelector('[role="radiogroup"]');
                if (radioGroup) {
                    fieldType = 'radio';
                    radioGroup.querySelectorAll('[role="radio"], [data-value]').forEach(radio => {
                        const labelEl = radio.querySelector('.aDTYNe, .docssharedWizToggleLabeledContent, span');
                        if (labelEl) {
                            const text = labelEl.textContent.trim();
                            if (text && !options.includes(text)) {
                                options.push(text);
                            }
                        }
                    });
                    selector = `[role="radiogroup"] [role="radio"]`;
                }
                
                // Check for checkboxes
                const checkGroup = container.querySelector('[role="list"]');
                if (checkGroup && !radioGroup) {
                    fieldType = 'checkbox';
                    checkGroup.querySelectorAll('[role="checkbox"]').forEach(cb => {
                        const labelEl = cb.querySelector('.aDTYNe, span');
                        if (labelEl) {
                            options.push(labelEl.textContent.trim());
                        }
                    });
                    selector = `[role="list"] [role="checkbox"]`;
                }
                
                // Check for dropdown
                const dropdown = container.querySelector('[role="listbox"]');
                if (dropdown) {
                    fieldType = 'dropdown';
                    dropdown.querySelectorAll('[role="option"]').forEach(opt => {
                        const text = opt.textContent.trim();
                        if (text) options.push(text);
                    });
                    selector = `[role="listbox"]`;
                }
                
                questions.push({
                    index: idx,
                    title: title,
                    description: description,
                    field_type: fieldType,
                    required: required,
                    options: options,
                    selector: selector
                });
            });
            
            return questions;
        }
        """
        
        try:
            raw_questions = await page.evaluate(js_code)
            
            self.questions = [
                GoogleFormQuestion(
                    index=q['index'],
                    title=q['title'],
                    description=q['description'],
                    field_type=q['field_type'],
                    required=q['required'],
                    options=q['options'],
                    selector=q['selector']
                )
                for q in raw_questions
            ]
            
            self.dispatcher.dispatch(Event(
                event_type=EventType.FIELD_EXTRACTED,
                message=f"Extracted {len(self.questions)} questions",
                data={"questions": [q.title for q in self.questions]}
            ))
            
            return self.questions
            
        except Exception as e:
            self.dispatcher.dispatch(Event(
                event_type=EventType.AGENT_ERROR,
                message=f"Failed to extract questions: {str(e)}",
                data={"error": str(e)}
            ))
            return []
    
    async def fill_question(
        self, 
        page: Any, 
        question: GoogleFormQuestion,
        context: Dict[str, Any]
    ) -> ActionResult:
        """Fill a single question in the form."""
        
        # Convert to FormField for strategy
        field = FormField(
            field_type=question.field_type,
            label=question.title,
            name=f"question_{question.index}",
            required=question.required,
            options=question.options,
            placeholder=question.description,
            selector=question.selector
        )
        
        # Get value from strategy
        value = await self.strategy.determine_field_value(field, context)
        
        try:
            if question.field_type == 'short_text':
                # Find and fill text input
                await self._fill_text_input(page, question, value)
            
            elif question.field_type == 'paragraph':
                # Find and fill textarea
                await self._fill_textarea(page, question, value)
            
            elif question.field_type == 'radio':
                # Click the matching radio option
                await self._select_radio(page, question, value)
            
            elif question.field_type == 'checkbox':
                # Check matching checkboxes
                await self._check_checkboxes(page, question, value)
            
            elif question.field_type == 'dropdown':
                # Select from dropdown
                await self._select_dropdown(page, question, value)
            
            question.filled = True
            question.value = value
            
            self.dispatcher.dispatch(Event(
                event_type=EventType.FIELD_FILLED,
                message=f"Filled: {question.title}",
                data={"question": question.title, "value": value}
            ))
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Filled question: {question.title}",
                data={"value": value}
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to fill '{question.title}': {str(e)}"
            )
    
    async def _fill_text_input(self, page: Any, question: GoogleFormQuestion, value: str):
        """Fill a short text input."""
        # Find the question container by title
        container = await self._find_question_container(page, question)
        if container:
            input_el = await container.query_selector('input[type="text"], input:not([type])')
            if input_el:
                await input_el.click()
                await input_el.fill(value)
                return
        
        # Fallback: try all text inputs
        inputs = await page.query_selector_all('input[type="text"]')
        for inp in inputs:
            try:
                await inp.fill(value)
                return
            except:
                continue
    
    async def _fill_textarea(self, page: Any, question: GoogleFormQuestion, value: str):
        """Fill a paragraph/textarea field."""
        container = await self._find_question_container(page, question)
        if container:
            textarea = await container.query_selector('textarea')
            if textarea:
                await textarea.click()
                await textarea.fill(value)
                return
        
        # Fallback
        textareas = await page.query_selector_all('textarea')
        for ta in textareas:
            try:
                await ta.fill(value)
                return
            except:
                continue
    
    async def _select_radio(self, page: Any, question: GoogleFormQuestion, value: str):
        """Select a radio button option."""
        container = await self._find_question_container(page, question)
        if container:
            # Find radio options
            radios = await container.query_selector_all('[role="radio"], [data-value]')
            for radio in radios:
                text = await radio.text_content()
                if text and value.lower() in text.lower():
                    await radio.click()
                    return
            
            # If no match, click first option
            if radios:
                await radios[0].click()
    
    async def _check_checkboxes(self, page: Any, question: GoogleFormQuestion, value: str):
        """Check checkbox options."""
        container = await self._find_question_container(page, question)
        if container:
            checkboxes = await container.query_selector_all('[role="checkbox"]')
            for cb in checkboxes:
                text = await cb.text_content()
                if text and value.lower() in text.lower():
                    await cb.click()
                    return
            
            # Default: check first if required
            if checkboxes and question.required:
                await checkboxes[0].click()
    
    async def _select_dropdown(self, page: Any, question: GoogleFormQuestion, value: str):
        """Select from dropdown."""
        container = await self._find_question_container(page, question)
        if container:
            listbox = await container.query_selector('[role="listbox"]')
            if listbox:
                await listbox.click()
                await asyncio.sleep(0.5)
                
                options = await page.query_selector_all('[role="option"]')
                for opt in options:
                    text = await opt.text_content()
                    if text and value.lower() in text.lower():
                        await opt.click()
                        return
                
                # Select first non-empty option
                for opt in options:
                    text = await opt.text_content()
                    if text and text.strip():
                        await opt.click()
                        return
    
    async def _find_question_container(self, page: Any, question: GoogleFormQuestion):
        """Find the container element for a question by its title."""
        containers = await page.query_selector_all('.Qr7Oae, .freebirdFormviewerComponentsQuestionBaseRoot')
        
        for container in containers:
            title_el = await container.query_selector('.M7eMe, [role="heading"]')
            if title_el:
                text = await title_el.text_content()
                if text and question.title in text:
                    return container
        
        return None
    
    async def fill_all(self, page: Any, context: Dict[str, Any]) -> List[ActionResult]:
        """Fill all questions in the form."""
        results = []
        
        for question in self.questions:
            result = await self.fill_question(page, question, context)
            results.append(result)
            await asyncio.sleep(0.5)  # Small delay between fields
        
        return results
    
    async def submit(self, page: Any) -> ActionResult:
        """Submit the Google Form."""
        try:
            # Find submit button
            submit_selectors = [
                '[role="button"]:has-text("Submit")',
                '.freebirdFormviewerViewNavigationSubmitButton',
                'div[role="button"] span:has-text("Submit")',
                'button:has-text("Submit")',
            ]
            
            for selector in submit_selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn:
                        await btn.click()
                        await asyncio.sleep(3)
                        
                        self.dispatcher.dispatch(Event(
                            event_type=EventType.FORM_SUBMITTED,
                            message="Form submitted successfully"
                        ))
                        
                        return ActionResult(
                            status=ActionStatus.SUCCESS,
                            message="Form submitted"
                        )
                except:
                    continue
            
            # Last resort: click any element with "Submit" text
            await page.click('text=Submit')
            await asyncio.sleep(3)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Form submitted (fallback)"
            )
            
        except Exception as e:
            self.dispatcher.dispatch(Event(
                event_type=EventType.FORM_SUBMISSION_ERROR,
                message=f"Submit failed: {str(e)}"
            ))
            
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Submit failed: {str(e)}"
            )

