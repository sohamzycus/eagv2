"""
Browser Actions implementing Template Method Pattern.

Each action follows the template:
1. validate() - Validate parameters
2. pre_execute() - Setup
3. execute() - Main action
4. post_execute() - Cleanup
"""

import asyncio
from typing import Any, Dict, List, Optional

from core.interfaces import BrowserAction, ActionResult, ActionStatus
from core.events import Event, EventType, EventDispatcher


class NavigateAction(BrowserAction):
    """Action to navigate to a URL."""
    
    def __init__(self):
        self.dispatcher = EventDispatcher()
    
    def validate(self, url: str = "", **kwargs) -> bool:
        """Validate URL is provided."""
        return bool(url) and url.startswith(("http://", "https://"))
    
    async def execute(self, page: Any, url: str = "", **kwargs) -> ActionResult:
        """Navigate to the URL."""
        try:
            wait_until = kwargs.get("wait_until", "networkidle")
            await page.goto(url, wait_until=wait_until, timeout=60000)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Navigated to {url}",
                data={"title": await page.title()}
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Navigation failed: {str(e)}"
            )


class ClickAction(BrowserAction):
    """Action to click an element."""
    
    def validate(self, selector: str = "", **kwargs) -> bool:
        """Validate selector is provided."""
        return bool(selector)
    
    async def execute(self, page: Any, selector: str = "", **kwargs) -> ActionResult:
        """Click the element."""
        try:
            await page.click(selector, timeout=10000)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Clicked {selector}"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Click failed: {str(e)}"
            )


class TypeAction(BrowserAction):
    """Action to type text into an element."""
    
    def validate(self, selector: str = "", text: str = "", **kwargs) -> bool:
        """Validate selector and text are provided."""
        return bool(selector)  # Allow empty text for clearing
    
    async def pre_execute(self, page: Any) -> None:
        """Clear the field before typing if requested."""
        pass
    
    async def execute(
        self, 
        page: Any, 
        selector: str = "", 
        text: str = "",
        clear_first: bool = True,
        **kwargs
    ) -> ActionResult:
        """Type text into the element."""
        try:
            if clear_first:
                await page.fill(selector, "")
            await page.fill(selector, text)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Typed into {selector}",
                data={"text_length": len(text)}
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Type failed: {str(e)}"
            )


class SelectAction(BrowserAction):
    """Action to select an option from a dropdown or radio group."""
    
    def validate(self, selector: str = "", value: str = "", **kwargs) -> bool:
        """Validate selector and value are provided."""
        return bool(selector) and bool(value)
    
    async def execute(
        self, 
        page: Any, 
        selector: str = "", 
        value: str = "",
        select_type: str = "dropdown",
        **kwargs
    ) -> ActionResult:
        """Select the option."""
        try:
            if select_type == "dropdown":
                await page.select_option(selector, value)
            elif select_type == "radio":
                # Click the radio button with matching value
                await page.click(f'{selector}[value="{value}"]')
            else:
                await page.click(selector)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Selected {value} in {selector}"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Select failed: {str(e)}"
            )


class ExtractFormAction(BrowserAction):
    """Action to extract form fields from the page."""
    
    def validate(self, **kwargs) -> bool:
        """No parameters needed."""
        return True
    
    async def execute(self, page: Any, **kwargs) -> ActionResult:
        """Extract form fields."""
        try:
            # JavaScript to extract Google Forms fields
            js_code = """
            () => {
                const fields = [];
                
                // For Google Forms specifically
                const formItems = document.querySelectorAll(
                    '[data-params], ' +
                    '.freebirdFormviewerComponentsQuestionBaseRoot, ' +
                    '.Qr7Oae'
                );
                
                formItems.forEach((item, idx) => {
                    // Get question text
                    const titleEl = item.querySelector(
                        '[role="heading"], ' +
                        '.freebirdFormviewerComponentsQuestionBaseTitle, ' +
                        '.M7eMe'
                    );
                    const title = titleEl ? titleEl.textContent.trim() : '';
                    
                    // Check for text input
                    const textInput = item.querySelector(
                        'input[type="text"], ' +
                        'input:not([type]), ' +
                        'textarea'
                    );
                    
                    // Check for radio buttons
                    const radioGroup = item.querySelector('[role="radiogroup"]');
                    
                    // Check for checkboxes
                    const checkboxGroup = item.querySelector('[role="group"]');
                    
                    // Check for dropdown
                    const dropdown = item.querySelector('[role="listbox"]');
                    
                    if (textInput) {
                        fields.push({
                            type: textInput.tagName === 'TEXTAREA' ? 'textarea' : 'text',
                            label: title,
                            name: textInput.name || `text_${idx}`,
                            selector: textInput.getAttribute('aria-labelledby') ? 
                                `[aria-labelledby="${textInput.getAttribute('aria-labelledby')}"]` :
                                `input[data-initial-value]`,
                            required: item.querySelector('[aria-label*="Required"]') !== null,
                            options: [],
                            placeholder: textInput.placeholder || ''
                        });
                    }
                    
                    if (radioGroup) {
                        const options = [];
                        radioGroup.querySelectorAll('[role="radio"]').forEach(radio => {
                            const label = radio.querySelector('.aDTYNe, .docssharedWizToggleLabeledContent') || 
                                         radio.querySelector('span');
                            if (label) options.push(label.textContent.trim());
                        });
                        
                        if (options.length > 0) {
                            fields.push({
                                type: 'radio',
                                label: title,
                                name: `radio_${idx}`,
                                selector: `[role="radiogroup"]`,
                                required: item.querySelector('[aria-label*="Required"]') !== null,
                                options: options
                            });
                        }
                    }
                    
                    if (checkboxGroup && !radioGroup) {
                        const options = [];
                        checkboxGroup.querySelectorAll('[role="checkbox"]').forEach(cb => {
                            const label = cb.closest('label')?.textContent?.trim() || 
                                         cb.querySelector('span')?.textContent?.trim();
                            if (label) options.push(label);
                        });
                        
                        if (options.length > 0) {
                            fields.push({
                                type: 'checkbox',
                                label: title,
                                name: `checkbox_${idx}`,
                                selector: `[role="group"]`,
                                required: item.querySelector('[aria-label*="Required"]') !== null,
                                options: options
                            });
                        }
                    }
                    
                    if (dropdown) {
                        const options = [];
                        dropdown.querySelectorAll('[role="option"]').forEach(opt => {
                            options.push(opt.textContent.trim());
                        });
                        
                        fields.push({
                            type: 'dropdown',
                            label: title,
                            name: `dropdown_${idx}`,
                            selector: `[role="listbox"]`,
                            required: item.querySelector('[aria-label*="Required"]') !== null,
                            options: options
                        });
                    }
                });
                
                // Fallback: try standard form elements
                if (fields.length === 0) {
                    document.querySelectorAll('input, textarea, select').forEach((el, idx) => {
                        fields.push({
                            type: el.type || 'text',
                            label: el.placeholder || el.name || '',
                            name: el.name || `field_${idx}`,
                            selector: el.id ? `#${el.id}` : `[name="${el.name}"]`,
                            required: el.required,
                            options: []
                        });
                    });
                }
                
                return fields;
            }
            """
            
            fields = await page.evaluate(js_code)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Extracted {len(fields)} form fields",
                data={"fields": fields}
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Extraction failed: {str(e)}"
            )


class ScreenshotAction(BrowserAction):
    """Action to take a screenshot."""
    
    def validate(self, path: str = "", **kwargs) -> bool:
        """Path is optional, will use default."""
        return True
    
    async def execute(
        self, 
        page: Any, 
        path: str = "screenshot.png",
        full_page: bool = True,
        **kwargs
    ) -> ActionResult:
        """Take a screenshot."""
        try:
            await page.screenshot(path=path, full_page=full_page)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Screenshot saved to {path}",
                data={"path": path}
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Screenshot failed: {str(e)}"
            )





