
# Definition of Sentiment Analysis AI Agent

We need to make a design document and specification for our AI agent. I want the to build an AI agent with Open AI SDK that analyzes sentiment of stock market news articles and provides insights. 
The agent should be able to fetch news articles from various sources, analyze the sentiment using natural language processing techniques, and generate a report summarizing the overall sentiment towards specific stocks or the market as a whole. 
The outputed report is going to serve as input for another AI agent that will make stock trading decisions based on the sentiment analysis provided. The report should include key metrics such as positive, negative, and neutral sentiment percentages, as well as reasoning behind the sentiment classification and recommendations for next action.

# Technology
- Python 3.12+
- OpenAI SDK
- Pydantic for data validation and model definition
- And more

# Architecture
The AI agent will be structured into several key components:
1. Data Source Collection Service: Responsible for fetching news articles from various sources (APIs, RSS feeds, web scraping).
2. Agent Toolset: A set of tools that the AI agent can use to interact with the data source collection service and perform sentiment analysis.
3. Sentiment Analysis Agent: The core AI agent that utilizes the toolset to analyze sentiment and generate reports.
4. Data Models: Pydantic models defining the structure of the data being processed and outputted by the agent.

### Data Models

We have defined Pydantic models used by the data source collection services and ai agents inside `sentiment_analysis_agent/models/` folder.

So all implementation of data sources and AI agents should use these models to ensure consistency and reliability of the data being processed by the AI agent.

# Data Sources

For data sources we will use precalculated sentiment from Alpha Vantage API. And then RSS feed from bing.

Each data source will be implemented as a separate class that adheres to a common interface. This will allow us to easily add or remove data sources in the future without affecting the overall architecture of the agent.

The components should have limit option to fetch only relevant number of articles for the given time window. When limit is in place, In case of Alpha Vantage API, it should return only top N articles with highest relevance score to the given ticker.

Service will offer in the interface option to get classified articles.

## #1 Alpha Vantage API

- We have mocks in `sentiment_analysis_agent/resources/mocks/alpha_vantage_mock.py`

Implementation Tasks:
Define Alpha Vantage Service class that will adhere to common data source interface. This service will fetch based on ticker and time range the sentiment data from Alpha Vantage API. 

The fetched data will be mapped to Pydantic models defined in `sentiment_analysis_agent/models/sentiment_analysis.py`.

Services that will fetch sentiment data for specific ticker from API and map it to SentimentContentScore model. It will allow the agent also filter out minimum relevance score to the ticker.

## News RSS Feed

We will also analyse news from Bing News Search: https://www.bing.com/news/search?q=AAPL&qft=interval%3d%228%22&form=PTFTNR

So the component for fetching news articles from RSS feed will be implemented as separate class adhering to common data source interface. It will fetch news articles based on ticker and lookback window (like 1W, 1M etc), and map them to SentimentContent defined in `sentiment_analysis_agent/models/sentiment_analysis.py`.


### Implementation Tasks

- Define a common interface for data sources that is easy to understand and extend.
- Implement cache mechanism to avoid fetching data for same ticker. Especially for API based sources with rate limits.
- Define data models using Pydantic for the data fetched from each source.
- Implement the Alpha Vantage API data source class.
- Implement the Bing News Search RSS feed data source class.

### Potential Development Ideas for News Sources

We could also analyse articles from these websites:

RSS Feeds:
- https://www.reuters.com/tools/rss
- https://seekingalpha.com/market_currents.xml
- https://www.marketwatch.com/rss/topstories

## Headlines Only
These feeds provide only headlines, but are easy to scrape:
https://seekingalpha.com/api/sa/combined/AAPL.xml
https://www.nasdaq.com/feed/rssoutbound?symbol=AAPL
https://news.google.com/rss/search?q=AAPL&hl=en-US&gl=US&ceid=US:en

# Bing News Search
But its infinite scroll, so might be tricky to scrape:
https://www.bing.com/news/search?q=AAPL&qft=interval%3d%228%22&form=PTFTNR

# Sentiment Classification Pipeline

For the sentiment content pipeline of individual articles/resources, we will create a service that takes single SentimentContent item and process it into SentimentContentScore by analyzing the sentiment using OpenAI SDK. 

In the pipeline, we will use a fine-tuned model for financial sentiment analysis.

Models to consider:
- https://huggingface.co/mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis?inference_provider=hf-inference
- https://huggingface.co/msr2903/mrm8488-distilroberta-fine-tuned-financial-sentiment

Services will be implemented as separate class that will take SentimentContent item and return SentimentContentScore item.


# AI Agent Implementation

The Sentiment Analysis Agent will be implemented using the OpenAI SDK. It will utilize the data source collection services to fetch news articles and sentiment data. The agent will then analyze the sentiment using natural language processing techniques and generate a report summarizing the overall sentiment towards specific stocks or the market as a whole.
