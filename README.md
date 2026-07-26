# HumanizedWord
OpenSource Humanizer for a generated content/text.

Building an open-source dataset and fine-tuning a small language model (SLM) to convert AI-generated text into natural, undetectable human text.

## 🛠️ Current Method
To ensure our dataset has 0% LLM contamination, we are:
1. Extracting pure human text from **pre-2014 Reddit/forums**.
2. Using an LLM to rewrite it into a robotic, "AI-style" format.
3. Creating training pairs: `[Input: AI Text ➔ Output: 2014 Human Text]`.

## 🆘 What I Need Help With (Mainly Data Collection)
Right now, the absolute focus is on gathering clean data. I need help with:
- Finding and extracting from other pre-2014 text sources (StackExchange, old blogs, etc.).
- Writing Python scripts to scrape, filter, and clean data (removing URLs, regex cleaning).
- Manually rewriting or annotating small batches of AI text into human text.

## 📜 How to Contribute
Want to help with the data or scripts? Follow these standard PR rules:

1. **Fork** this repository.
2. **Clone** your fork: `git clone https://github.com/YOUR-USERNAME/HumanizedWord.git`
3. **Create a branch**: `git checkout -b feature/add-reddit-scraper` (or whatever you're working on).
4. **Commit**: `git commit -m "Added script for data extraction"`
5. **Push & Open a PR** to the `main` branch.

*Note: If you are adding a huge dataset or making big changes, please open an Issue first so we can discuss it!*