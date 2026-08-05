import re

def get_canonical_subject_id(name):
    """
    Normalizes any subject string variant to its canonical uppercase core identifier.
    Examples:
        "Dwm L", "DWM Lab", "DWM Practical", "DWM" -> "DWM"
        "AI Lab", "AI L", "AI" -> "AI"
        "Wcn L", "WC Lab", "Wc" -> "WCN"
    """
    if not name:
        return ""
    clean = str(name).strip()
    patterns = [
        r'\s+(PRACTICALS|PRACTICAL|LABS|LAB|L)$',
        r'_(PRACTICALS|PRACTICAL|LABS|LAB|L)$',
        r'-(PRACTICALS|PRACTICAL|LABS|LAB|L)$'
    ]
    clean_upper = clean.upper()
    for p in patterns:
        clean_upper = re.sub(p, '', clean_upper)
    clean_upper = clean_upper.replace('-', '').replace('_', '').replace(' ', '')
    return clean_upper


class FailureRecord:
    def __init__(self, division, batch, subject, teacher=None, lab=None, stage="Pre-Generation", reason="Unspecified", resource_report=None):
        self.division = division
        self.batch = batch or "ALL"
        self.subject = subject or "UNKNOWN"
        self.teacher = teacher or "NOT FOUND"
        self.lab = lab or "NOT ASSIGNED"
        self.stage = stage
        self.reason = reason
        self.resource_report = resource_report

    def to_exception_message(self, solver_status="NOT RUN", variables_status="INCOMPLETE"):
        msg = (
            f"\n\nTIMETABLE GENERATION FAILED\n\n"
            f"Division : {self.division}\n"
            f"Batch : {self.batch}\n"
            f"Subject : {self.subject}\n"
            f"Teacher : {self.teacher}\n"
            f"Lab : {self.lab}\n"
            f"Variables : {variables_status}\n"
            f"Solver : {solver_status}\n"
            f"Validation : {self.stage}\n\n"
            f"Reason :\n"
            f"{self.reason}\n"
        )
        if self.resource_report:
            msg += f"\n==================================================\n{self.resource_report}\n"
        return msg


def print_step1_curriculum(class_key, theory_subjects, lab_subjects):
    print("\n=================================================")
    print(f"DIVISION : {class_key}")
    print("=================================================")
    print("\nRequired Theory")
    total_theory_slots = 0
    if not theory_subjects:
        print("  (None)")
    else:
        for s in theory_subjects:
            req = int(s.get('weeklyLectures') or s.get('lecturesPerWeek') or s.get('weekly_lectures') or 3)
            total_theory_slots += req
            print(f"{s['name']} = {req}")

    print("\n-------------------------")
    print("Required Labs")
    total_lab_slots = 0
    if not lab_subjects:
        print("  (None)")
    else:
        for s in lab_subjects:
            total_lab_slots += 1
            print(f"{s['name']} = 1")

    print("\n-------------------------")
    print("Expected Total")
    print(f"Theory = {total_theory_slots}")
    print(f"Labs = {total_lab_slots}")
    print("=================================================\n")


def print_step2_teacher_mapping(class_key, theory_subjects, lab_subjects, subject_teachers_map):
    print(f"Teacher Mapping ({class_key})")
    all_mapped = True
    missing_items = []

    for s in theory_subjects:
        sname = s['name']
        teachers = subject_teachers_map.get(sname, [])
        if teachers:
            print(f"{sname} Theory -> {', '.join(teachers)}")
        else:
            print(f"{sname} Theory -> [MISSING]")
            all_mapped = False
            missing_items.append((sname, 'Theory'))

    for s in lab_subjects:
        sname = s['name']
        teachers = subject_teachers_map.get(sname, [])
        if teachers:
            print(f"{sname} Lab -> {', '.join(teachers)}")
        else:
            print("\nERROR")
            print("Teacher mapping missing")
            print("Subject")
            print(f"{sname}")
            print("No teacher assigned\n")
            all_mapped = False
            missing_items.append((sname, 'Lab'))

    return all_mapped, missing_items


def print_step3_variable_creation(class_key, lab_subjects, creation_results):
    print(f"\nCreating Variables\n{class_key}")
    for s in lab_subjects:
        sname = s['name']
        res = creation_results.get(sname, {})
        if res.get('created'):
            print(f"{sname}\nCreated [OK]")
        else:
            reason = res.get('reason', 'Unknown reason')
            print("\nERROR")
            print("Variable never created")
            print("Subject")
            print(f"{sname}")
            print("Reason")
            print(f"{reason}\n")


def print_step4_attempt(div, batch, subject, teacher, lab, day, slot, result, failure_reason=None):
    print("\nAttempt")
    print("Division")
    print(f"{div}")
    print("Batch")
    print(f"{batch}")
    print("Subject")
    print(f"{subject}")
    print("Teacher")
    print(f"{teacher or 'NOT FOUND'}")
    print("Lab")
    print(f"{lab or 'NOT ASSIGNED'}")
    print("Day")
    print(f"{day}")
    print("Slot")
    print(f"{slot}")
    print("Result")
    print(f"{result}")
    if failure_reason and result == "FAILURE":
        print("Reason")
        print(f"{failure_reason}")


def print_step5_rejected_candidate(day, slot, reason):
    print(f"Rejected\n{day}\nSlot {slot}\nReason\n{reason}")


def print_step6_model_statistics(theory_vars, lab_vars, teacher_cons, room_cons, lab_cons, batch_cons):
    print("\nModel Statistics")
    print(f"Theory Variables\n{theory_vars}")
    print(f"Lab Variables\n{lab_vars}")
    print(f"Teacher Constraints\n{teacher_cons}")
    print(f"Room Constraints\n{room_cons}")
    print(f"Lab Constraints\n{lab_cons}")
    print(f"Batch Constraints\n{batch_cons}\n")


def print_step7_solver_status(status_str):
    print("\nSolver Status")
    print(f"{status_str}\n")


def print_step8_lab_coverage(class_key, subject_reports):
    print(f"\nLab Coverage\n{class_key}")
    for rep in subject_reports:
        sname = rep['subject']
        req = rep['required']
        sched = rep['scheduled']
        status = "PASS" if rep['pass'] else "FAIL"
        print(f"{sname}\nRequired\n{req}\nScheduled\n{sched}\n{status}\n-----------------")


def print_step9_failure_summary(failures_list):
    print("\nFAILURE SUMMARY")
    for item in failures_list:
        print("Division")
        print(f"{item.get('division', 'Unknown')}")
        print("Missing")
        print(f"{item.get('subject', 'Unknown')}")
        print("Reason")
        print(f"{item.get('reason', 'Unknown')}")
        print("----------------------------")
    if failures_list:
        root_cause = failures_list[0].get('root_cause', 'Constraint or Resource Mismatch')
        print(f"Root Cause\n{root_cause}\n")


def print_step10_timeline(stages):
    print("\nGeneration Timeline\n")
    stage_idx = 1
    for stage_name, (ok, reason) in stages.items():
        if ok:
            print(f"Stage {stage_idx}\n{stage_name} [OK]")
        else:
            print(f"Stage {stage_idx}\n{stage_name} Failed")
            if reason:
                print(f"Reason\n{reason}")
        stage_idx += 1
    print()


def format_step11_exception(div, batch, subject, teacher, lab, day_slot, variables_status, solver_status, validation_stage, exact_reason):
    return (
        f"\n\nTIMETABLE GENERATION FAILED\n\n"
        f"Division : {div}\n"
        f"Batch : {batch or 'ALL'}\n"
        f"Subject : {subject or 'UNKNOWN'}\n"
        f"Teacher : {teacher or 'NOT FOUND'}\n"
        f"Lab : {lab or 'NOT ASSIGNED'}\n"
        f"Variables : {variables_status}\n"
        f"Solver : {solver_status}\n"
        f"Validation : {validation_stage}\n\n"
        f"Reason :\n"
        f"{exact_reason}\n"
    )
