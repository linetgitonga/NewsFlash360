# NewsFlash360 🌐

A comprehensive news aggregation and fact-checking platform focused on Kenyan news, featuring multi-source content collection, AI-powered analysis, and community engagement.

## 🚀 Features

### News Aggregation & Summarization
- Automated scraping from multiple sources:
  - Social media (Twitter, Facebook, Reddit, Telegram)
  - Blogs and news websites
  - Community radio transcripts
- Multi-lingual support (English, Swahili, Sheng)
- AI-powered content summarization

### 🤖 AI & Fact-Checking
- Real-time fact-checking of viral claims
- Integration with fact-checking databases
- Misinformation detection using ML models
- NLP-based claim extraction and classification

### 👥 Community Features
- User-submitted news and alerts
- Community forum with moderation
- Content rating and verification system
- Geographic news clustering

## 🛠️ Technical Stack

### Backend
- Django REST Framework
- PostgreSQL
- Redis (for caching)
- Celery (for async tasks)

### Data Collection
- Social media APIs (Twitter, Facebook, Reddit, Telegram)
- Web scraping (BeautifulSoup4, Selenium)
- NLP processing (spaCy, Transformers)

### Authentication & Security
- JWT-based authentication
- Role-based access control
- Content moderation system

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/linetgitonga/newsflash360.git
cd newsflash360
```

2. Create and activate virtual environment:
```bash
python -m venv virtualenv
source virtualenv/bin/activate  # Linux/Mac
.\virtualenv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## 🔧 Configuration

### Required Environment Variables
- Database configuration
- Social media API credentials
- AWS S3 credentials (for media storage)
- Email settings
- Redis configuration

### API Credentials Setup
1. Twitter API (v2)
2. Facebook Graph API
3. Reddit API
4. Telegram API

## 🚀 Running the Scrapers

Start the scraping pipeline:
```bash
python run_scraper_pipe.py
```

Individual scrapers can be run with:
```bash
python run_twitter_scraper.py
python run_facebook_scraper.py
python run_reddit_scraper.py
python run_telegram_scraper.py
```

## 📝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name (@linetgitonga@github.com)

## 🙏 Acknowledgments

- Twitter API
- Facebook Graph API
- Reddit API
- Telegram API
- Django community
- Open-source contributors

## 📞 Support

For support, email support@newsflash360.com or join our Slack channel.
