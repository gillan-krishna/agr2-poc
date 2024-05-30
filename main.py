# Third-party imports
# import openai
from groq import Groq
from fastapi import FastAPI, Form, Depends
from decouple import config
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Internal imports
from models import Conversation, SessionLocal
from utils import send_message, logger


app = FastAPI()
# Set up the OpenAI API client
# openai.api_key = config("OPENAI_API_KEY")
groq_api_key = config("GROQ_KEY")

whatsapp_number = config("TO_NUMBER")

# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.post("/message")
async def reply(Body: str = Form(), db: Session = Depends(get_db)):
    # Call the OpenAI API to generate text with GPT-3.5
    # response = openai.Completion.create(
    #     engine="gpt-3.5-turbo-instruct",
    #     prompt=Body,
    #     max_tokens=200,
    #     n=1,
    #     stop=None,
    #     temperature=0.5,
    # )

    client = Groq(
        api_key=groq_api_key,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": Body,
            }
        ],
        model="llama3-8b-8192",
    )


    # The generated text
    # chat_response = response.choices[0].text.strip()
    chat_response = chat_completion.choices[0].message.content

    # Store the conversation in the database
    try:
        conversation = Conversation(
            sender=whatsapp_number,
            message=Body,
            response=chat_response
            )
        db.add(conversation)
        db.commit()
        logger.info(f"Conversation #{conversation.id} stored in database")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error storing conversation in database: {e}")
    send_message(whatsapp_number, chat_response)
    return ""