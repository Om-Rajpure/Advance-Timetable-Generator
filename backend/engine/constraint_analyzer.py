"""
Constraint Resource Analysis Engine

Analyzes unscheduled theory lectures and practical labs when timetable scheduling
is incomplete or infeasible. Determines bottlenecks across:
1. Teacher Shortage
2. Classroom Shortage
3. Lab Shortage
4. Constraint Conflict
5. Invalid Data

Generates a detailed Resource Recommendation Report and a Minimum Additional Resources Needed Summary.
"""

import math
from collections import defaultdict


class ConstraintAnalyzer:
    """Analyzes timetable generation failures and calculates minimum required resources."""

    def __init__(self, context, global_state=None, cpsat_result=None, lab_failures=None, startup_failures=None):
        self.context = context or {}
        self.branch_data = self.context.get("branchData", {})
        self.smart_input = self.context.get("smartInputData", {})
        self.global_state = global_state
        self.cpsat_result = cpsat_result or {}
        self.lab_failures = lab_failures or []
        self.startup_failures = startup_failures or []

        self.working_days = self.branch_data.get("workingDays", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        if not isinstance(self.working_days, list) or not self.working_days:
            self.working_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        self.slots_per_day = self.branch_data.get("slotsPerDay") or self.branch_data.get("periodsPerDay") or 7
        self.total_weekly_slots_per_div = len(self.working_days) * self.slots_per_day

        # Classrooms
        self.classrooms = self.branch_data.get("classrooms") or self.branch_data.get("rooms") or []
        if isinstance(self.classrooms, dict):
            self.classrooms = list(self.classrooms.keys())

        # Labs
        self.labs = self.branch_data.get("labs") or []

        # Subjects and Teachers
        self.subjects = self.smart_input.get("subjects", [])
        self.teachers = self.smart_input.get("teachers", [])
        self.teacher_map = self._build_teacher_map()

    def _build_teacher_map(self):
        t_map = defaultdict(list)
        mapping_list = self.smart_input.get("teacherSubjectMap", [])
        for m in mapping_list:
            sname = m.get("subjectName") or m.get("subject")
            tname = m.get("teacherName") or m.get("teacher")
            if sname and tname and tname not in t_map[sname]:
                t_map[sname].append(tname)

        # Fallback to teacher profile subjects
        for t in self.teachers:
            tname = t.get("name")
            for sname in t.get("subjects", []):
                if sname and tname and tname not in t_map[sname]:
                    t_map[sname].append(tname)
        return t_map

    def analyze(self, target_division=None):
        """
        Perform complete bottleneck analysis.

        Returns:
            dict: Structured analysis result with text report and resource summary.
        """
        # Determine unscheduled theory and practical items
        unscheduled_theory = self._extract_unscheduled_theory(target_division)
        unscheduled_practicals = self._extract_unscheduled_practicals(target_division)

        # Determine primary affected division
        division_name = target_division
        if not division_name:
            all_affected_divs = list(set([item['division'] for item in unscheduled_theory + unscheduled_practicals]))
            if all_affected_divs:
                division_name = all_affected_divs[0] if len(all_affected_divs) == 1 else f"{all_affected_divs[0]} (+{len(all_affected_divs)-1} others)"
            else:
                division_name = "Overall Institute"

        theory_remaining_count = sum(item['missing'] for item in unscheduled_theory)
        practicals_remaining_count = sum(item['missing'] for item in unscheduled_practicals)

        # Perform 5 Bottleneck Category Analyses
        teacher_reqs, teacher_summary_additions = self._analyze_teacher_shortages(unscheduled_theory, unscheduled_practicals)
        lab_reqs, lab_summary_additions = self._analyze_lab_shortages(unscheduled_practicals)
        room_reqs, room_summary_additions = self._analyze_classroom_shortages(unscheduled_theory)
        bottlenecks, other_summary_additions = self._analyze_constraint_conflicts(unscheduled_theory, unscheduled_practicals)
        invalid_data_issues = self._analyze_invalid_data()

        # Combine teacher requirements from invalid data (unmapped teachers)
        for issue in invalid_data_issues:
            if "teacher" in issue.lower() and issue not in teacher_reqs:
                teacher_reqs.append(f"• {issue}")

        # Compute Actionable Suggested Fixes
        suggested_fixes = self._generate_suggested_fixes(
            teacher_reqs, lab_reqs, room_reqs, bottlenecks, invalid_data_issues,
            teacher_summary_additions, lab_summary_additions, room_summary_additions, other_summary_additions
        )

        # Resource Summary
        resource_summary = {
            "teachers": teacher_summary_additions if teacher_summary_additions else ["None"],
            "labs": lab_summary_additions if lab_summary_additions else ["None"],
            "classrooms": room_summary_additions if room_summary_additions else ["None"],
            "other": other_summary_additions if other_summary_additions else ["None"]
        }

        # Build full report object
        report_data = {
            "division": division_name,
            "reasonForFailure": {
                "theoryRemaining": theory_remaining_count,
                "practicalsRemaining": practicals_remaining_count,
                "details": [
                    f"✓ Theory lectures remaining: {theory_remaining_count}",
                    f"✓ Practicals remaining: {practicals_remaining_count}"
                ]
            },
            "teacherRequirements": teacher_reqs if teacher_reqs else ["• No critical teacher shortages identified."],
            "labRequirements": lab_reqs if lab_reqs else ["• No critical lab shortages identified."],
            "classroomRequirements": room_reqs if room_reqs else ["• No critical classroom shortages identified."],
            "constraintBottlenecks": bottlenecks if bottlenecks else ["• Standard constraint limits applied."],
            "invalidData": invalid_data_issues,
            "suggestedFixes": suggested_fixes,
            "resourceSummary": resource_summary
        }

        # Generate Plain Text Report string
        report_text = self.format_text_report(report_data)
        report_data["reportText"] = report_text

        return report_data

    def _extract_unscheduled_theory(self, target_division):
        results = []
        incomplete_cpsat = self.cpsat_result.get("incomplete", [])
        for div, subj, placed, needed in incomplete_cpsat:
            if target_division and div != target_division:
                continue
            missing = max(0, needed - placed)
            if missing > 0:
                results.append({
                    "division": div,
                    "subject": subj,
                    "placed": placed,
                    "needed": needed,
                    "missing": missing,
                    "type": "Theory"
                })
        return results

    def _extract_unscheduled_practicals(self, target_division):
        results = []
        for fail in self.lab_failures:
            div = getattr(fail, "division", None) or (fail.get("division") if isinstance(fail, dict) else "UNKNOWN")
            if target_division and div != target_division:
                continue
            subj = getattr(fail, "subject", None) or (fail.get("subject") if isinstance(fail, dict) else "Lab Subject")
            batch = getattr(fail, "batch", None) or (fail.get("batch") if isinstance(fail, dict) else "All Batches")
            results.append({
                "division": div,
                "subject": subj,
                "batch": batch,
                "missing": 1,
                "type": "Practical"
            })
        return results

    def _analyze_teacher_shortages(self, unscheduled_theory, unscheduled_practicals):
        reqs = []
        summary_additions = []

        # Check theory & lab subjects with unplaced lectures/practicals
        unplaced_by_subject = defaultdict(int)
        for item in unscheduled_theory + unscheduled_practicals:
            sname = item['subject']
            unplaced_by_subject[sname] += item['missing']

        for sname, count in unplaced_by_subject.items():
            mapped_teachers = self.teacher_map.get(sname, [])
            is_lab = any("lab" in sname.lower() or "practical" in sname.lower() or item.get("type") == "Practical" for item in unscheduled_practicals if item['subject'] == sname)
            subj_type_str = "Lab" if is_lab else "Theory"

            # Avoid redundant "DWM Theory Theory" or "BT Lab Lab"
            if subj_type_str.lower() in sname.lower():
                display_name = sname
            else:
                display_name = f"{sname} {subj_type_str}"

            if not mapped_teachers:
                reqs.append(f"• {display_name} requires 1 additional qualified teacher.")
                summary_additions.append(f"+1 {display_name} Teacher")
            else:
                # Check teacher utilization & availability limits
                all_teachers_maxed = True
                teacher_avail_details = []

                for tname in mapped_teachers:
                    t_info = next((t for t in self.teachers if t.get("name") == tname), {})
                    max_weekly = t_info.get("maxWeeklyLectures") or t_info.get("maxHours") or 20
                    
                    # Calculate assigned slots
                    assigned = 0
                    if self.global_state:
                        assigned = sum(1 for (t, d, s) in getattr(self.global_state, "teacher_assignments", {}).keys() if t == tname)

                    if assigned < max_weekly:
                        all_teachers_maxed = False
                    
                    teacher_avail_details.append((tname, assigned, max_weekly))

                if all_teachers_maxed:
                    main_teacher = mapped_teachers[0]
                    reqs.append(f"• {display_name} requires 1 additional teacher OR increase availability of {main_teacher}.")
                    summary_additions.append(f"+1 {display_name} Teacher")
                else:
                    names_str = " / ".join(mapped_teachers)
                    reqs.append(f"• {display_name}: Increase available slots/periods for teacher(s) {names_str} to resolve schedule clashes.")

        return reqs, summary_additions

    def _analyze_lab_shortages(self, unscheduled_practicals):
        reqs = []
        summary_additions = []

        if not unscheduled_practicals:
            return reqs, summary_additions

        lab_count = len(self.labs)
        if lab_count == 0:
            reqs.append("• No dedicated laboratories configured in institute facility setup.")
            summary_additions.append("+1 Computer / Shared Lab")
        else:
            for item in unscheduled_practicals:
                sname = item['subject']
                div = item['division']
                reqs.append(f"• Need 1 additional lab for {sname} ({div}) OR existing labs have zero free consecutive 2-period slots.")

            # Summary addition
            needed_labs = min(2, math.ceil(len(unscheduled_practicals) / 2))
            summary_additions.append(f"+{needed_labs} Computer/Subject Lab")

        return reqs, summary_additions

    def _analyze_classroom_shortages(self, unscheduled_theory):
        reqs = []
        summary_additions = []

        if not unscheduled_theory:
            return reqs, summary_additions

        room_count = len(self.classrooms)
        bd_divisions = self.branch_data.get("divisions", {})
        total_divisions_count = sum(len(divs) for divs in bd_divisions.values()) if isinstance(bd_divisions, dict) else 1

        if room_count < total_divisions_count:
            shortage = total_divisions_count - room_count
            reqs.append(f"• Institute classroom count ({room_count}) is less than total parallel divisions ({total_divisions_count}). Need {shortage} additional classroom(s).")
            summary_additions.append(f"+{shortage} Classroom")
        else:
            reqs.append("• Need additional classroom availability during peak period slots.")

        return reqs, summary_additions

    def _analyze_constraint_conflicts(self, unscheduled_theory, unscheduled_practicals):
        bottlenecks = []
        other_additions = []

        # Check total slots vs curriculum demand
        total_available_slots = self.total_weekly_slots_per_div
        total_demand = sum(s.get("weeklyLectures", 3) for s in self.subjects)
        
        # Max lectures per day
        max_daily = self.branch_data.get("maxLecturesPerDay") or self.slots_per_day
        if total_demand > (len(self.working_days) * max_daily):
            bottlenecks.append(f"• Total required subject lectures ({total_demand}) exceed maximum weekly capacity ({len(self.working_days) * max_daily}).")
            other_additions.append(f"Relax max lectures/day or add 1 working day.")

        if unscheduled_practicals:
            bottlenecks.append("• Continuous 2-period lab constraint cannot be satisfied without clashing with recess or existing theory slots.")

        # Check high teacher utilization
        for t in self.teachers:
            tname = t.get("name")
            if self.global_state:
                assigned = sum(1 for (t_item, d, s) in getattr(self.global_state, "teacher_assignments", {}).keys() if t_item == tname)
                max_w = t.get("maxWeeklyLectures") or 20
                if assigned >= max_w and max_w > 0:
                    bottlenecks.append(f"• Teacher {tname} has reached 100% workload utilization ({assigned}/{max_w} slots).")
                    other_additions.append(f"Increase Teacher {tname} availability by 3-4 periods.")

        return bottlenecks, list(set(other_additions))

    def _analyze_invalid_data(self):
        issues = []

        # Startup failures / missing teacher mappings
        for s in self.subjects:
            sname = s.get("name")
            if sname and not self.teacher_map.get(sname):
                issues.append(f"Subject '{sname}' has no mapped teacher in teacherSubjectMap.")

        for fail in self.startup_failures:
            reason = getattr(fail, "reason", str(fail))
            issues.append(f"Startup Data Error: {reason}")

        return issues

    def _generate_suggested_fixes(self, teacher_reqs, lab_reqs, room_reqs, bottlenecks, invalid_data,
                                  t_summary, l_summary, r_summary, o_summary):
        fixes = []
        step = 1

        # Invalid Data fixes
        for issue in invalid_data:
            if "no mapped teacher" in issue.lower():
                sname = issue.split("'")[1] if "'" in issue else "subject"
                fixes.append(f"{step}. Assign a qualified teacher for subject '{sname}' in Teacher-Subject Mapping.")
                step += 1

        # Teacher fixes
        for item in t_summary:
            if item != "None":
                fixes.append(f"{step}. Add {item.replace('+', '')}.")
                step += 1

        # Lab fixes
        for item in l_summary:
            if item != "None":
                fixes.append(f"{step}. Add {item.replace('+', '')} or free up consecutive period blocks.")
                step += 1

        # Room fixes
        for item in r_summary:
            if item != "None":
                fixes.append(f"{step}. Add {item.replace('+', '')}.")
                step += 1

        # Other / Constraint fixes
        for item in o_summary:
            if item != "None":
                fixes.append(f"{step}. {item}")
                step += 1

        if not fixes:
            fixes.append("1. Verify teacher availability schedules and ensure no double-booking across divisions.")
            fixes.append("2. Add 1 additional lab or classroom facility.")

        return fixes

    def format_text_report(self, report_data):
        """Format the report into clean markdown text matching required specification."""
        div = report_data.get("division", "BE-B")
        reason = report_data.get("reasonForFailure", {})
        t_reqs = report_data.get("teacherRequirements", [])
        l_reqs = report_data.get("labRequirements", [])
        c_reqs = report_data.get("classroomRequirements", [])
        b_reqs = report_data.get("constraintBottlenecks", [])
        fixes = report_data.get("suggestedFixes", [])
        summary = report_data.get("resourceSummary", {})

        lines = []
        lines.append("RESOURCE ANALYSIS")
        lines.append("")
        lines.append(f"Division: {div}")
        lines.append("")
        lines.append("Reason for Failure:")
        for d in reason.get("details", []):
            lines.append(f"{d}")
        lines.append("")
        lines.append("Teacher Requirements")
        lines.append("--------------------")
        for item in t_reqs:
            lines.append(f"{item}")
        lines.append("")
        lines.append("Lab Requirements")
        lines.append("----------------")
        for item in l_reqs:
            lines.append(f"{item}")
        lines.append("")
        lines.append("Classroom Requirements")
        lines.append("----------------------")
        for item in c_reqs:
            lines.append(f"{item}")
        lines.append("")
        lines.append("Constraint Bottlenecks")
        lines.append("----------------------")
        for item in b_reqs:
            lines.append(f"{item}")
        lines.append("")
        lines.append("Suggested Fixes")
        lines.append("---------------")
        for f in fixes:
            lines.append(f"{f}")
        lines.append("")
        lines.append("==================================================")
        lines.append("MINIMUM ADDITIONAL RESOURCES NEEDED")
        lines.append("==================================================")
        lines.append("")
        lines.append("Teachers:")
        for t in summary.get("teachers", ["None"]):
            lines.append(f"{t}")
        lines.append("")
        lines.append("Labs:")
        for l in summary.get("labs", ["None"]):
            lines.append(f"{l}")
        lines.append("")
        lines.append("Classrooms:")
        for c in summary.get("classrooms", ["None"]):
            lines.append(f"{c}")
        lines.append("")
        lines.append("Other:")
        for o in summary.get("other", ["None"]):
            lines.append(f"{o}")

        return "\n".join(lines)
