import json

from crewai.tools import BaseTool


class EducationTools:
    class CurriculumGapAnalyzer(BaseTool):
        name: str = "Gap Analyzer"
        description: str = "Compares SA CAPS against Global Standards to find missing skills."

        def _run(self, grade_level: str) -> str:
            # Load Local Libraries
            try:
                with open("data/education/sa_caps_baseline.json") as f:
                    sa_data = json.load(f)
                with open("data/education/global_future_skills.json") as f:
                    global_data = json.load(f)
            except FileNotFoundError:
                return "Error: Curriculum databases not found."

            grade_key = grade_level.lower().replace(" ", "_")

            if grade_key not in sa_data or grade_key not in global_data:
                return f"Data not available for {grade_level}"

            # The Analysis Logic
            sa_curr = sa_data[grade_key]
            global_curr = global_data[grade_key]

            gap_report = {
                "grade": grade_level,
                "current_sa_focus": list(sa_curr.keys()),
                "missing_critical_skills": [],
                "sellable_opportunity": "",
            }

            # Perform a proper gap analysis by finding skills in global standards not in SA curriculum.
            sa_all_skills = {skill for skills_list in sa_curr.values() for skill in skills_list}
            global_all_skills = {skill for skills_list in global_curr.values() for skill in skills_list}

            missing_skills = list(global_all_skills - sa_all_skills)
            gap_report["missing_critical_skills"] = sorted(missing_skills)

            gap_report["sellable_opportunity"] = (
                f"Create a 'Term 1 Future Pack' covering: {', '.join(gap_report['missing_critical_skills'][:3])}"
            )

            return json.dumps(gap_report, indent=2)

    class SyllabusGenerator(BaseTool):
        name: str = "Syllabus Creator"
        description: str = "Generates a Term 1 Lesson Plan for the identified gaps."

        def _run(self, gap_analysis_json: str) -> str:
            data = json.loads(gap_analysis_json)
            skills = data["missing_critical_skills"]

            # Create the product outline
            syllabus = f"""
            # VAAL AI EMPIRE: TERM 1 FUTURE PACK
            ## Target: {data["grade"]} | Price: Low Cost (Digital Delivery)

            ### Module 1: {skills[0]}
            - Week 1: Introduction & Concepts
            - Week 2: Practical Application (No computer needed option)
            - Week 3: Digital Simulation

            ### Module 2: {skills[1]}
            - Week 4: The Psychology of {skills[1]}
            - Week 5: Real world case studies

            ### Module 3: {skills[2]}
            - Week 6: Building the Future
            - Week 7: Final Project
            """
            return syllabus
