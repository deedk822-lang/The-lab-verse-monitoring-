import logging

from crewai import Agent, Crew, Process, Task

logger = logging.getLogger(__name__)


class NumeraiAgentCrew:
    """
    CrewAI orchestration for Numerai signal generation using Agentic Research API
    """

    def __init__(self, perplexity_devkit, finnhub_fetcher):
        self.perplexity = perplexity_devkit
        self.finnhub = finnhub_fetcher

        # Initialize agents
        self.data_analyst = self._create_data_analyst()
        self.financial_researcher = self._create_financial_researcher()
        self.signal_generator = self._create_signal_generator()
        self.fact_checker = self._create_fact_checker()

    def _create_data_analyst(self) -> Agent:
        return Agent(
            role="Data Analyst",
            goal="Analyze market news, SEC filings, and price data to identify trends",
            backstory="""You are an expert data analyst with 15 years of experience 
            analyzing financial markets. You leverage the Perplexity Agentic Research API 
            to find real-time, verified information.""",
            verbose=True,
            allow_delegation=False,
        )

    def _create_financial_researcher(self) -> Agent:
        return Agent(
            role="Financial Researcher",
            goal="Research company fundamentals and financial metrics",
            backstory="""You are a seasoned financial researcher who specializes 
            in fundamental analysis. You have deep expertise in reading financial 
            statements and understanding company valuation.""",
            verbose=True,
            allow_delegation=False,
        )

    def _create_signal_generator(self) -> Agent:
        return Agent(
            role="Signal Generator",
            goal="Generate high-quality Numerai predictions based on research",
            backstory="""You are a quantitative analyst specializing in the Numerai 
            tournament. You understand the unique requirements of Numerai signals 
            and how to generate predictions that perform well.""",
            verbose=True,
            allow_delegation=False,
        )

    def _create_fact_checker(self) -> Agent:
        return Agent(
            role="Fact Checker",
            goal="Verify all claims and data quality before signal submission",
            backstory="""You are a meticulous fact-checker who ensures all data 
            is accurate and all claims are verified.""",
            verbose=True,
            allow_delegation=False,
        )

    def generate_signals(self, tickers: list[str]) -> dict:
        """Main workflow to generate Numerai signals"""

        logger.info(f"Generating signals for {len(tickers)} tickers")

        # Task 1: Analyze market data (Agentic)
        analyze_task = Task(
            description=f"""Analyze market news and SEC filings for: {', '.join(tickers[:5])}
            
            1. Fetch latest news using Perplexity Agentic Research API (batch queries)
            2. Retrieve SEC 10-Q filings for recent quarters via web_search
            3. Identify key trends, sentiment, and risks
            """,
            agent=self.data_analyst,
            expected_output="Structured analysis with news sentiment and SEC insights",
        )

        # Task 2: Research fundamentals
        research_task = Task(
            description=f"""Research company fundamentals for: {', '.join(tickers[:5])}
            
            1. Fetch financial metrics using Finnhub
            2. Extract P/E ratio, revenue growth, EPS
            """,
            agent=self.financial_researcher,
            expected_output="Financial metrics comparison table",
        )

        # Task 3: Generate signals
        signal_task = Task(
            description="""Generate Numerai signals based on analysis and research.
            Signals must be between 0 and 1.
            """,
            agent=self.signal_generator,
            expected_output="Numerai signals in required format",
        )

        # Task 4: Fact check
        verify_task = Task(
            description="""Verify all data and signals before submission.
            Check that signals are within [0,1] range and data sources are cited.
            """,
            agent=self.fact_checker,
            expected_output="Verification report with quality score",
        )

        # Create crew and execute
        crew = Crew(
            agents=[
                self.data_analyst,
                self.financial_researcher,
                self.signal_generator,
                self.fact_checker,
            ],
            tasks=[analyze_task, research_task, signal_task, verify_task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        logger.info("Signal generation complete")
        return result
