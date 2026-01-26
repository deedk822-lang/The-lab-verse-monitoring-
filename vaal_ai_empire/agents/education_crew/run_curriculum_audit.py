import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from edu_tools import EducationTools

# 1. Setup
llm = ChatOpenAI(model="gpt-4-turbo", api_key=os.getenv("OPENAI_API_KEY"))

# 2. Define Agents

# Agent A: The Auditor (Sub-division: Search & Compare)
auditor = Agent(
    role="Curriculum Auditor",
    goal="Identify exactly what South African education is missing compared to the 1st world",
    backstory="You are an expert in comparative pedagogy. You look at CAPS and cry, then you look at Finland and see the future.",
    tools=[EducationTools.CurriculumGapAnalyzer()],
    llm=llm,
    verbose=True,
)

# Agent B: The Architect (Sub-division: Enhance & Create)
architect = Agent(
    role="Educational Product Architect",
    goal="Create a low-cost, high-value Term 1 syllabus that fills the identified gaps",
    backstory="You design educational products that sell. You know how to package complex AI/Finance topics for kids.",
    tools=[EducationTools.SyllabusGenerator()],
    llm=llm,
    verbose=True,
)

# 3. Define Tasks

# Task 1: Spot the Gap
task_audit = Task(
    description="Analyze 'Grade 10'. Compare SA CAPS to Global Standards. Identify the specific missing skills.",
    expected_output="A JSON report detailing the Skills Gap.",
    agent=auditor,
)

# Task 2: Create the Product (Human Verification Step)
task_design = Task(
    description="""
    Take the Skills Gap Report.
    Design a 'Term 1 Brighter Future' package.
    It must be sellable as a PDF download.
    Include specific lesson outlines.
    """,
    expected_output="A Markdown formatted Course Outline ready for sale.",
    agent=architect,
    context=[task_audit],
    human_input=True,  # <--- CRITICAL: YOU MUST APPROVE THE CURRICULUM
)

# 4. The Crew
education_crew = Crew(
    agents=[auditor, architect], tasks=[task_audit, task_design], process=Process.sequential, verbose=True
)

# 5. Execution
if __name__ == "__main__":
    print("\n🎓 INITIALIZING SABC EDUCATION HYBRID UNIT...\n")
    result = education_crew.kickoff()

    # Save the Final Product
    os.makedirs("output/education", exist_ok=True)
    with open("output/education/Term_1_Package_Grade_10.md", "w") as f:
        f.write(str(result))

    print("\n✅ PRODUCT GENERATED. Saved to output/education/Term_1_Package_Grade_10.md")
