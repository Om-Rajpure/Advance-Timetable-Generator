import os
import sys
import time
from playwright.sync_api import sync_playwright

# Reconfigure stdout/stderr to support emojis on Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Setup artifact paths
ARTIFACT_DIR = r"C:\Users\omraj\.gemini\antigravity\brain\ce218470-64c2-4b1c-9ec5-eb36b3c0d28d"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def take_screenshot(page, name):
    path = os.path.join(ARTIFACT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"📸 Screenshot saved: {name}.png")

def test_workflow():
    print("🚀 Starting Web UI Workflow Test...")
    
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        # Create a clean context
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        # Navigate to frontend login page
        print("Navigating to http://localhost:3000/login...")
        page.goto("http://localhost:3000/login", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        # Take initial screenshot
        take_screenshot(page, "01_login_page")
        
        # Login
        print("Logging in as om...")
        page.fill("input#username", "om")
        page.fill("input#password", "om@123")
        take_screenshot(page, "02_login_filled")
        
        page.click("button.btn-auth")
        page.wait_for_timeout(2000)
        
        # Assert dashboard loaded
        print("Current URL:", page.url)
        take_screenshot(page, "03_dashboard")
        
        # Check if we need to setup branch
        print("Checking branch setup status...")
        setup_btn = page.locator("button.setup-branch-btn")
        if setup_btn.count() > 0 or "branch-setup" in page.url:
            print("Branch setup is needed. Starting branch setup wizard...")
            if setup_btn.count() > 0:
                setup_btn.click()
                page.wait_for_timeout(1000)
        else:
            # Let's navigate to /branch-setup directly to configure it exactly as requested
            print("Navigating to /branch-setup to ensure correct configuration...")
            page.goto("http://localhost:3000/branch-setup")
            page.wait_for_timeout(1000)
            
        print("Wizard: Step 1 - Branch Identity")
        take_screenshot(page, "04_branch_setup_step1")
        # Fill branch name
        page.fill("input", "Computer Engineering") # Form field for branchName
        page.click("button.btn-wizard-next")
        page.wait_for_timeout(1000)
        
        print("Wizard: Step 2 - Academic Years")
        take_screenshot(page, "05_branch_setup_step2")
        # SE, TE, BE should be checked by default. Let's click Next.
        page.click("button.btn-wizard-next")
        page.wait_for_timeout(1000)
        
        print("Wizard: Step 3 - Divisions & Batches")
        take_screenshot(page, "06_branch_setup_step3")
        
        # We need to set Batches: SE=2, TE=3, BE=3
        # In Step3Divisions, we have a list of division cards: SE, TE, BE.
        # Let's find the card for SE and click the minus button on Batches number stepper.
        # Inside Step3Divisions.jsx, the batches stepper is the second number-stepper inside the division card.
        # Let's target the stepper buttons by locating the division-card for SE.
        # The cards are rendered in order: SE (index 0), TE (index 1), BE (index 2).
        # Inside each division-card, there are two number-steppers:
        # 1. Division stepper (first number-stepper)
        # 2. Batch stepper (second number-stepper inside batch-config-section)
        # Let's target the minus button of the batch stepper for SE (index 0) to change from 3 to 2.
        se_card = page.locator(".division-card").nth(0)
        batch_stepper = se_card.locator(".batch-config-section .number-stepper")
        minus_btn = batch_stepper.locator("button.stepper-button").nth(0)
        minus_btn.click()
        page.wait_for_timeout(500)
        print("SE batches count decremented to 2.")
        take_screenshot(page, "07_branch_setup_step3_batches_configured")
        
        page.click("button.btn-wizard-next")
        page.wait_for_timeout(1000)
        
        print("Wizard: Step 4 - Schedule")
        take_screenshot(page, "08_branch_setup_step4")
        # Keep defaults and click Next
        page.click("button.btn-wizard-next")
        page.wait_for_timeout(1000)
        
        print("Wizard: Step 5 - Recess")
        take_screenshot(page, "09_branch_setup_step5")
        # Configure Break Duration = 45 minutes
        # Find the select for recessDuration (it's the second select on the page)
        # Or look at all selects and pick the one with duration options
        page.select_option("select:has-text('minutes')", label="45 minutes")
        take_screenshot(page, "10_branch_setup_step5_recess_configured")
        
        page.click("button.btn-wizard-next")
        page.wait_for_timeout(1000)
        
        print("Wizard: Step 6 - Rooms & Labs")
        take_screenshot(page, "11_branch_setup_step6")
        
        # Configure Classrooms = 5. Currently it has 4 default classrooms.
        # Let's add Room-104.
        # Room input has placeholder "e.g. Room-101, LH-5"
        room_input = page.locator("input[placeholder*='LH-5']")
        room_input.fill("Room-104")
        page.locator("button.btn-add").nth(0).click() # The add classroom button is the first btn-add
        page.wait_for_timeout(500)
        print("Added classroom Room-104.")
        
        # Configure Labs = 6. Currently it has 2 default labs.
        # We need to add 4 more labs.
        # Lab name input has placeholder "New Lab Name (e.g., Physics Lab)"
        lab_name_input = page.locator("input[placeholder*='Physics Lab']")
        # Lab capacity input has placeholder "Cap."
        lab_cap_input = page.locator("input[placeholder='Cap.']")
        # Add Lab button is the btn-add in labs section (index 1)
        add_lab_btn = page.locator("button:has-text('Add Lab')")
        
        new_labs = ["Chemistry Lab", "ME Lab", "Electrical Lab", "Civil Lab"]
        for lab in new_labs:
            lab_name_input.fill(lab)
            lab_cap_input.fill("30")
            add_lab_btn.click()
            page.wait_for_timeout(500)
            print(f"Added lab: {lab}")
            
        take_screenshot(page, "12_branch_setup_step6_rooms_configured")
        
        page.click("button.btn-wizard-next")
        page.wait_for_timeout(1000)
        
        print("Wizard: Step 7 - Review")
        take_screenshot(page, "13_branch_setup_step7")
        
        # Confirm & Save
        page.click("button:has-text('Confirm & Save')")
        print("Saving branch configuration...")
        page.wait_for_timeout(3000)
        
        # Redirected to Smart Input page
        print("Current URL:", page.url)
        take_screenshot(page, "14_smart_input_page")
        
        # Go to File Upload (csv) tab
        print("Navigating to File Upload tab...")
        page.locator(".tab-button:has-text('File Upload')").click()
        page.wait_for_timeout(1000)
        take_screenshot(page, "15_file_upload_tab")
        
        # Upload the three files
        # The CsvUploader has three upload cards
        # Let's locate the file input element.
        # Typically they are input[type=file]
        
        # Let's get the absolute paths of the files in project root
        project_dir = r"c:\Users\omraj\OneDrive\Desktop\Laptop\Projects\Adv Timetable Gen"
        teachers_file = os.path.join(project_dir, "Teachers_demo.xlsx")
        subjects_file = os.path.join(project_dir, "Subjects1.xlsx")
        mappings_file = os.path.join(project_dir, "Mapping_demo.xlsx")
        
        # Check if files exist
        for f in [teachers_file, subjects_file, mappings_file]:
            if not os.path.exists(f):
                print(f"❌ ERROR: File not found: {f}")
                sys.exit(1)
        
        # Upload Teachers
        print("Selecting Teachers upload card...")
        page.locator(".upload-card").nth(0).click()
        page.wait_for_timeout(500)
        print("Uploading Teachers_demo.xlsx...")
        page.locator("input[type='file']").set_input_files(teachers_file)
        page.wait_for_timeout(1500)
        confirm_btn = page.locator("button:has-text('Confirm & Add')")
        if confirm_btn.count() > 0:
            confirm_btn.click()
            page.wait_for_timeout(500)
        
        # Upload Subjects
        print("Selecting Subjects upload card...")
        page.locator(".upload-card").nth(1).click()
        page.wait_for_timeout(500)
        print("Uploading Subjects1.xlsx...")
        page.locator("input[type='file']").set_input_files(subjects_file)
        page.wait_for_timeout(1500)
        if confirm_btn.count() > 0:
            confirm_btn.click()
            page.wait_for_timeout(500)
        
        # Upload Mappings
        print("Selecting Mappings upload card...")
        page.locator(".upload-card").nth(2).click()
        page.wait_for_timeout(500)
        print("Uploading Mapping_demo.xlsx...")
        page.locator("input[type='file']").set_input_files(mappings_file)
        page.wait_for_timeout(1500)
        if confirm_btn.count() > 0:
            confirm_btn.click()
            page.wait_for_timeout(500)
        
        take_screenshot(page, "16_files_uploaded")
        
        # Click "Confirm Data"
        confirm_btn = page.locator("button.btn-confirm-data")
        confirm_btn.click()
        page.wait_for_timeout(1000)
        print("Data confirmed.")
        take_screenshot(page, "17_data_confirmed")
        
        # Click "Finish & Generate"
        generate_btn = page.locator("button.btn-add-system")
        print("Clicking 'Finish & Generate'...")
        generate_btn.click()
        
        # Wait for timetable generation (this takes some time, up to 60 seconds)
        print("Waiting for timetable generation to complete...")
        try:
            page.wait_for_url("**/timetable", timeout=60000)
            page.wait_for_timeout(3000) # Give it 3s to render the grids completely
            print("Successfully navigated to timetable page!")
        except Exception as e:
            print("Timed out or error waiting for redirection:", str(e))
        
        # Take final screenshot on timetable view page
        take_screenshot(page, "18_generation_completed")
        print("Current URL after generation:", page.url)
        
        browser.close()
        print("🎉 Web UI Workflow Test completed successfully!")

if __name__ == "__main__":
    test_workflow()
