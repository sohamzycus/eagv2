"""
Browser Controller - Manages browser lifecycle and provides high-level API.

Uses Factory pattern to create browser instances.
"""

import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from core.events import Event, EventType, EventDispatcher
from core.interfaces import ActionResult, ActionStatus


class BrowserController:
    """
    High-level controller for browser automation.
    
    Manages:
    - Browser lifecycle (launch, close)
    - Page navigation
    - Screenshot capture
    - Form extraction
    """
    
    def __init__(
        self,
        headless: bool = False,
        slow_mo: int = 100,
        screenshots_dir: str = "screenshots",
        viewport: Dict[str, int] = None
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.viewport = viewport or {"width": 1280, "height": 800}
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._dispatcher = EventDispatcher()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.launch()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def launch(self) -> None:
        """Launch the browser."""
        self._playwright = await async_playwright().start()
        
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ]
        )
        
        self._context = await self._browser.new_context(
            viewport=self.viewport,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self._page = await self._context.new_page()
        
        self._dispatcher.dispatch(Event(
            event_type=EventType.BROWSER_LAUNCHED,
            message="Browser launched successfully",
            data={"headless": self.headless}
        ))
    
    async def close(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        self._dispatcher.dispatch(Event(
            event_type=EventType.BROWSER_CLOSED,
            message="Browser closed"
        ))
    
    @property
    def page(self) -> Page:
        """Get the current page."""
        if not self._page:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self._page
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> ActionResult:
        """Navigate to a URL."""
        self._dispatcher.dispatch(Event(
            event_type=EventType.NAVIGATION_START,
            message=f"Navigating to {url}",
            data={"url": url}
        ))
        
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=60000)
            await asyncio.sleep(2)  # Wait for dynamic content
            
            self._dispatcher.dispatch(Event(
                event_type=EventType.NAVIGATION_COMPLETE,
                message=f"Navigation complete: {url}",
                data={"url": url, "title": await self.page.title()}
            ))
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Navigated to {url}",
                data={"title": await self.page.title()}
            )
        except Exception as e:
            self._dispatcher.dispatch(Event(
                event_type=EventType.NAVIGATION_ERROR,
                message=f"Navigation failed: {str(e)}",
                data={"url": url, "error": str(e)}
            ))
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Navigation failed: {str(e)}"
            )
    
    async def screenshot(self, name: str = "screenshot") -> str:
        """Take a screenshot."""
        path = self.screenshots_dir / f"{name}.png"
        await self.page.screenshot(path=str(path), full_page=True)
        
        self._dispatcher.dispatch(Event(
            event_type=EventType.SCREENSHOT_CAPTURED,
            message=f"Screenshot saved: {path}",
            data={"path": str(path)}
        ))
        
        return str(path)
    
    async def extract_form_fields(self) -> List[Dict[str, Any]]:
        """Extract all form fields from the current page."""
        # JavaScript to extract form fields
        js_code = """
        () => {
            const fields = [];
            
            // Find all input fields
            document.querySelectorAll('input, textarea, select').forEach((el, idx) => {
                const field = {
                    type: el.tagName.toLowerCase() === 'select' ? 'dropdown' : 
                          (el.type || 'text'),
                    name: el.name || el.id || `field_${idx}`,
                    label: '',
                    required: el.required || false,
                    options: [],
                    placeholder: el.placeholder || '',
                    selector: '',
                    value: el.value || ''
                };
                
                // Try to find label
                if (el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) field.label = label.textContent.trim();
                }
                
                // Fallback: look for parent label or nearby text
                if (!field.label) {
                    const parent = el.closest('label');
                    if (parent) field.label = parent.textContent.trim();
                }
                
                // For Google Forms, find the question text
                if (!field.label) {
                    const formItem = el.closest('[data-params]') || 
                                     el.closest('.freebirdFormviewerComponentsQuestionBaseRoot');
                    if (formItem) {
                        const questionText = formItem.querySelector('[role="heading"]') ||
                                            formItem.querySelector('.freebirdFormviewerComponentsQuestionBaseTitle');
                        if (questionText) field.label = questionText.textContent.trim();
                    }
                }
                
                // Build selector
                if (el.id) {
                    field.selector = `#${el.id}`;
                } else if (el.name) {
                    field.selector = `[name="${el.name}"]`;
                } else {
                    field.selector = `${el.tagName.toLowerCase()}:nth-of-type(${idx + 1})`;
                }
                
                // Get options for select/radio/checkbox
                if (el.tagName.toLowerCase() === 'select') {
                    field.options = Array.from(el.options).map(o => o.textContent.trim());
                }
                
                fields.push(field);
            });
            
            // Find radio button groups
            const radioGroups = {};
            document.querySelectorAll('input[type="radio"]').forEach(radio => {
                const name = radio.name;
                if (!radioGroups[name]) {
                    radioGroups[name] = {
                        type: 'radio',
                        name: name,
                        label: '',
                        options: [],
                        selector: `input[name="${name}"]`
                    };
                    
                    // Find the group's question
                    const container = radio.closest('[role="radiogroup"]') || 
                                     radio.closest('.freebirdFormviewerComponentsQuestionRadioRoot');
                    if (container) {
                        const title = container.closest('[data-params]')?.querySelector('[role="heading"]');
                        if (title) radioGroups[name].label = title.textContent.trim();
                    }
                }
                
                // Get option label
                const label = radio.closest('label') || 
                             radio.parentElement?.querySelector('span');
                if (label) {
                    radioGroups[name].options.push(label.textContent.trim());
                }
            });
            
            // Add radio groups to fields
            Object.values(radioGroups).forEach(group => {
                if (group.options.length > 0) {
                    fields.push(group);
                }
            });
            
            return fields;
        }
        """
        
        try:
            fields = await self.page.evaluate(js_code)
            
            self._dispatcher.dispatch(Event(
                event_type=EventType.FIELD_EXTRACTED,
                message=f"Extracted {len(fields)} form fields",
                data={"field_count": len(fields)}
            ))
            
            return fields
        except Exception as e:
            self._dispatcher.dispatch(Event(
                event_type=EventType.AGENT_ERROR,
                message=f"Failed to extract fields: {str(e)}",
                data={"error": str(e)}
            ))
            return []
    
    async def fill_field(
        self, 
        selector: str, 
        value: str, 
        field_type: str = "text"
    ) -> ActionResult:
        """Fill a form field with the given value."""
        try:
            if field_type == "text" or field_type == "textarea" or field_type == "email" or field_type == "url":
                await self.page.fill(selector, value)
            elif field_type == "radio":
                # For radio buttons, click the option with matching value
                await self.page.click(f'{selector}[value="{value}"]')
            elif field_type == "checkbox":
                await self.page.check(selector)
            elif field_type == "dropdown" or field_type == "select":
                await self.page.select_option(selector, value)
            else:
                # Default to fill
                await self.page.fill(selector, value)
            
            self._dispatcher.dispatch(Event(
                event_type=EventType.FIELD_FILLED,
                message=f"Filled field {selector}",
                data={"selector": selector, "value": value[:50] + "..." if len(value) > 50 else value}
            ))
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Filled field: {selector}"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to fill field {selector}: {str(e)}"
            )
    
    async def click(self, selector: str) -> ActionResult:
        """Click an element."""
        try:
            await self.page.click(selector)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Clicked: {selector}"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to click {selector}: {str(e)}"
            )
    
    async def submit_form(self, submit_selector: str = None) -> ActionResult:
        """Submit the current form."""
        try:
            if submit_selector:
                await self.page.click(submit_selector)
            else:
                # Try common submit button selectors
                selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    '[role="button"]:has-text("Submit")',
                    'button:has-text("Submit")',
                    '.freebirdFormviewerViewNavigationSubmitButton',
                ]
                
                for sel in selectors:
                    try:
                        element = await self.page.query_selector(sel)
                        if element:
                            await element.click()
                            break
                    except:
                        continue
            
            await asyncio.sleep(3)  # Wait for submission
            
            self._dispatcher.dispatch(Event(
                event_type=EventType.FORM_SUBMITTED,
                message="Form submitted successfully"
            ))
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Form submitted"
            )
        except Exception as e:
            self._dispatcher.dispatch(Event(
                event_type=EventType.FORM_SUBMISSION_ERROR,
                message=f"Form submission failed: {str(e)}",
                data={"error": str(e)}
            ))
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Form submission failed: {str(e)}"
            )
    
    async def get_page_content(self) -> str:
        """Get the current page HTML content."""
        return await self.page.content()
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """Wait for a selector to appear."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False





