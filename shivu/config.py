class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "6835013483"
    sudo_users = "6835013483", "5421067814", "6835013483"
    GROUP_ID = -1002104939708
    TOKEN = "7456960988:AAF2qtGunhDGWzwLRX7Izq4GON_2kS_uxPw"
    mongo_url = "mongodb+srv://nudewaifubot:nudewaifubot@nude.50fk0.mongodb.net/?retryWrites=true&w=majority&appName=nude"
    PHOTO_URL = ["https://ibb.co/q7jzMwz", "https://ibb.co/T2qNx5m", "https://ibb.co/TYS7yC4", "https://ibb.co/hVRR0T1", "https://ibb.co/3W3rVy6"]
    SUPPORT_CHAT = "Dyna_community"
    UPDATE_CHAT = "Seizer_updates"
    BOT_USERNAME = "waifu_pro_bot"
    CHARA_CHANNEL_ID = "-1002335814239"
    api_id = 24698455
    api_hash = "00d4cd57b1fb369ea65563d40c9c2494"

    # New Administration System
    GRADE4 = []
    GRADE3 = ["7334126640"]
    GRADE2 = ["6305653111", "5421067814"]
    GRADE1 = ["7004889403", "1374057577", "5158013355", "5630057244", "7334126640"]
    SPECIALGRADE = ["6835013483","1993290981"]

    Genin = []
    Chunin = []
    Jonin = ["7334126640"]
    Hokage = ["5421067814"]
    Akatsuki = ["6402009857", "5158013355" , "5630057244"]
    Princess = ["1993290981"]
    
    STRICT_GBAN = True
    ALLOW_CHATS = True
    ALLOW_EXCL = True
    DEL_CMDS = True
    INFOPIC = True

class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
