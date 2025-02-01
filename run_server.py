import uvicorn
import os
from dotenv import load_dotenv
from mlb_storyteller.main import app

load_dotenv()

# This is the app that will be used by gunicorn
app = app

if __name__ == "__main__":
    # This is only used for local development
    uvicorn.run(
        app,
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', '8080')),
        reload=True
    ) 