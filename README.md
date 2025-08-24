# Vietnamese-StockInsight

## 🧑‍🤝‍🧑Group members
- Trình Cao An - 22127004
- Nguyễn Kim Anh - 22127014
- Võ Thị Kim Khôi - 22127214

## 📖Project Description
In the data-driven financial market, the automated extraction and synthesis of information from unstructured news sources is a critical yet challenging task. Vietnamese stock market is experiencing rapid growth, accompanied by an significant increase in the volume of unstructured textual data. Manually processing this vast amount of information to extract timely and relevant insights is practically impossible. This project presents an system, using  Natural Language Processing (NLP), to transform raw Vietnamese financial news articles into structured, actionable intelligence reports.

## 📌Project Objectives
- Constructing a NER dataset for Vietnamese financial domain.
- Fine-tuning and provide a comparative analysis of different Transformer architectures (phoBERT vs XLM-R) for the financial NER task.
- Building a structured Knowledge Base from the raw text corpus by applying the trained NER models.
- Developing an sentiment analysis model capable of identifying sentiment towards specific entities (stock codes, company...).
- Integrating all components into an interactive web application that can generate analysis reports for any given stock code.

## 📊Data
All datasets for this project can be found here: [startlearning](https://drive.google.com/drive/folders/1Yo1gVdMeYXkhVb3G5pkMNIlYL9gWsjeK?usp=sharing)

## 🤖Fine-tuned models used in this porject
- phoBERT for NER: [AnTrinh/my-phobert-ner](https://huggingface.co/AnTrinh/my-phobert-ner)
- XLM-Roberta for NER: [PuppetLover/XLM-Roberta\NER](https://huggingface.co/PuppetLover/XLM-Roberta_NER)
- phoBERT for sentiment analysis: [VTKK/phobert-sentiment-analysis](https://huggingface.co/VTKK/phobert-sentiment-analysis)

## 📂Project Structure
```
Vietnamese-StockInsight/
|-- app/        # Source code for the web app
│-- data/       # stock codes data files
│-- database/   # Knowledge Base data files
│-- training/   # Model training scripts and notebooks
│-- .env        # Environment configuration file
│-- README.md   # Project overview
│-- docker-compose.yml     # Docker configuration
```
## 🌐Web Application
### 🚀Hosted Version: [Stock Insights 🔮](https://puppetlover-stockinsights.hf.space/)

### ▶️Run the App
#### 1. Prerequisites:
- Python $\geq$ 3.10 and `pip` available on your system.
- (Recommended) A virtual environment created with `venv` or `conda`.
- Required configuration via environment variables or `.env` file:
    - `FIREBASE_SERVICE_ACCOUNT` (JSON string or path) for server-side token verification.
    - `MONGODB_URI` for user/profile storage.
    - `GEMINI_API_KEY` (optional) if summary generation is enabled.
    - `KB_DB_PATH` pointing to the SQLite knowledge-base file.
#### 2. Installation:
1. Clone or download the project source code.
2. (Optional) Create and activate a virtual environment.
3. Install all dependencies: 
```bash
pip install -r requirements.txt
```

From the project’s `/app` directory, start Streamlit:
```bash
streamlit run app.py
```
By default, Streamlit serves the UI at [`http://localhost:8501`](http://localhost:8501). Press `Ctrl+C` in the terminal to stop the server.
