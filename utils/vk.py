import vk_api
from vk_api.utils import get_random_id
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VKNotificationBot:
    def __init__(self, token):
        """Инициализация бота с сервисным токеном."""
        self.vk_session = vk_api.VkApi(token=token)
        self.vk = self.vk_session.get_api()

    def send_notifications(self, user_ids, message):
        """Отправка push-уведомлений группе пользователей."""
        if not user_ids:
            logger.warning("Список ID пользователей пуст.")
            return False

        if len(message) > 200:
            logger.warning("Сообщение превышает 200 символов, усекается.")
            message = message[:200]

        try:
            result = self.vk.secure.sendNotification(
                user_ids=','.join(map(str, user_ids)),
                message=message,
                random_id=get_random_id()
            )
            logger.info(f"Уведомление отправлено: {result}")
            return result
        except vk_api.ApiError as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")
            return False

    def send_messages(self, user_ids, message):
        """Отправка текстовых сообщений в чат."""
        sent_count = 0
        for user_id in user_ids:
            try:
                self.vk.messages.send(
                    user_id=user_id,
                    message=message,
                    random_id=get_random_id()
                )
                sent_count += 1
                logger.info(f"Сообщение отправлено пользователю {user_id}")
                time.sleep(0.34)  # Ограничение: не более 3 запросов/сек
            except vk_api.ApiError as e:
                logger.error(f"Ошибка при отправке пользователю {user_id}: {e}")
        logger.info(f"Отправлено сообщений: {sent_count} из {len(user_ids)}")
        return sent_count

# Пример использования
if __name__ == "__main__":
    # Замените на свой токен приложения
    TOKEN = "ваш_сервисный_токен"
    bot = VKNotificationBot(TOKEN)

    # Список ID сотрудников (пример)
    employee_ids = [123456, 789012, 345678]
    message = "Напоминание: собрание в 15:00. Подробности в корпоративной почте."

    # Отправка push-уведомлений
    bot.send_notifications(employee_ids, message)

    # Альтернативно: отправка сообщений в чат
    bot.send_messages(employee_ids, message)