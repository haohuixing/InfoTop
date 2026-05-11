# Template readme file for now....

## What to do:

### Download the file
- Either download zip or use git clone

### cd to the directory 
- In command prompt enter cd directory/to/the/files

### Install dependencies
- pip install -r requirements.txt

### Edit .env.example:
- Rename `.env.example` to `.env`
- Edit all the things in `.env` to whatever you have for yourself
- **DO NOT** publish your `.env` online, it probably has some sensitive information!

### Run the database init file  to set up the database 
- Run python init_db.py

### Run the fastapi program
- Type in cmd prompt "uvicorn app:app --reload" to run the file OR "python app.py"

### Go to localhost:8000

## Plan features:

- Make website and dashboard so users can select what they want to be notified of in their report
  - Halfway done rightnow, we have primitive. 
  - Still need login/signup and such 
- Implementation of middle-end AI LLM to process reports better instead of just gathering raw data and then stuffing it into a report
- Include a readmefile on setting up database?
- Add payment methods
- Add "custom orders" for market warnings
- Add more "stories" to the story page
