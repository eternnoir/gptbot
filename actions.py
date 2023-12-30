import time
import asyncio
from openai.types import beta
from aiogram import types
from client import client, get_thread, get_assistant
from logger import create_logger
from users import check_user
from translate import _t

logger = create_logger("actions")


async def change_assistant(message: types.Message):
  tutor = message.text
  user_id = message.from_user.id
  await message.answer(_t("bot.your_tutor", tutor=tutor), reply_markup=types.ReplyKeyboardRemove())
  assistant = await get_assistant(user_id, tutor)
  logger.info(f"new_assistant:{user_id}:{tutor}:{assistant.id}")


async def handle_response(message: types.Message):
  user_id = message.from_user.id
  username = message.from_user.username
  if check_user(user_id, username):
    return await message.answer(_t("bot.not_allowed", id=user_id))

  logger.info(f"user:{username}:{user_id}\n\t{message.md_text}")

  thread = await get_thread(user_id)
  logger.debug(thread)

  await add_message_to_thread(thread, message)

  assistant = await get_assistant(user_id)
  logger.debug(assistant)

  await create_run(thread, assistant, message)


async def create_run(thread: beta.Thread, assistant: beta.Assistant, message: types.Message):
  run = await client.beta.threads.runs.create(
      thread.id,
      assistant_id=assistant.id,
      instructions=_t("gpt.instructions", name=message.from_user.first_name)
  )

  start_time = time.time()
  while True:
    logger.info(f"status:{run.status}")

    if run.status == "completed":
      await retrieve_messages(thread.id, run.id, message)
      logger.info("done")
      break
    elif run.status in ["failed", "cancelled", "expired"]:
      logger.info("failed")
      break
    else:
      await asyncio.sleep(1)

    run = await client.beta.threads.runs.retrieve(
        run.id,
        thread_id=thread.id
    )
  end_time = time.time()
  logger.debug(f"reponse time: {end_time - start_time:.2f}s")


async def retrieve_messages(thread_id, run_id, message: types.Message):
  run_steps = await client.beta.threads.runs.steps.list(
      thread_id=thread_id,
      run_id=run_id
  )

  for step in run_steps.data:
    if step.type == "message_creation":
      message_id = step.step_details.message_creation.message_id

      msg = await client.beta.threads.messages.retrieve(
          message_id=message_id,
          thread_id=thread_id
      )

      content = msg.content[0].text.value
      if content:
        await message.answer(content)
        logger.info(f"{msg.role}:{step.assistant_id}:\n\t{content}")


async def add_message_to_thread(thread: beta.Thread, message: types.Message):
  user_request = await client.beta.threads.messages.create(
      thread.id,
      role="user",
      content=message.md_text
  )
  logger.debug(user_request)
