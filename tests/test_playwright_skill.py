import pytest
from pathlib import Path
from autogen_playwright.skills.playwright_skill import PlaywrightSkill

@pytest.fixture
def skill():
    """Create a PlaywrightSkill instance for testing"""
    return PlaywrightSkill()

def test_start_session(skill):
    """Test browser session initialization"""
    try:
        result = skill.start_session("Test Scenario")
        assert "successfully" in result.lower(), "Session start should return success message"
        assert skill.browser is not None, "Browser should be initialized"
        assert skill.context is not None, "Context should be initialized"
        assert skill.page is not None, "Page should be initialized"
    finally:
        # Clean up after this test
        if hasattr(skill, 'page') and skill.page:
            skill.end_session()

def test_navigation(skill):
    """Test page navigation"""
    try:
        skill.start_session("Navigation Test")
        test_url = "https://example.com"
        skill.navigate(test_url)
        assert test_url in skill.page.url, f"URL should contain {test_url}, got {skill.page.url}"
    finally:
        if hasattr(skill, 'page') and skill.page:
            skill.end_session()

def test_element_interaction(skill):
    """Test element interactions"""
    try:
        skill.start_session("Element Test")
        skill.navigate("https://example.com")
        
        assert skill.verify_element_exists("h1"), "H1 element should exist"
        assert not skill.verify_element_exists("non-existent-element"), "Non-existent element should not be found"
        assert skill.verify_text_content("Example Domain"), "Page should contain 'Example Domain'"
        assert not skill.verify_text_content("Non-existent Text"), "Page should not contain non-existent text"
    finally:
        if hasattr(skill, 'page') and skill.page:
            skill.end_session()

def test_screenshot(skill):
    """Test screenshot functionality"""
    try:
        skill.start_session("Screenshot Test")
        skill.navigate("https://example.com")
        
        screenshot_name = "test_screenshot"
        skill.take_screenshot(screenshot_name)
        assert Path(f"{screenshot_name}.png").exists(), "Screenshot file should be created"
    finally:
        if hasattr(skill, 'page') and skill.page:
            skill.end_session()
        # Clean up the screenshot
        screenshot_path = Path(f"{screenshot_name}.png")
        if screenshot_path.exists():
            screenshot_path.unlink()

def test_error_handling(skill):
    """Test error handling scenarios"""
    try:
        skill.start_session("Error Test")
        skill.navigate("https://example.com")  # Navigate to a valid site first
        
        # Test with invalid selectors - should not raise exceptions but return error info
        result = skill.click_element("#non-existent")
        assert "Error" in result or "Failed" in result or "not found" in result.lower()
        
        result = skill.verify_element_exists("#non-existent")
        assert not result, "Non-existent element should not be found"
        
        # Test form filling with invalid selector
        with pytest.raises(Exception):
            skill.fill_form("#non-existent", "test value")
    finally:
        if hasattr(skill, 'page') and skill.page:
            skill.end_session()