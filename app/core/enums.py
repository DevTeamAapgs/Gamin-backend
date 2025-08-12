from enum import IntEnum, Enum
import string   

class Status(IntEnum):
    """Status enum for active/inactive records"""
    INACTIVE = 0
    ACTIVE = 1

class DeletionStatus(IntEnum):
    """Deletion status enum for soft delete functionality"""
    DELETED = 0
    NOT_DELETED = 1 
    
class PlayerType(IntEnum):
    """PlayerType enum for superadmin/admin employee/player records"""
    SUPERADMIN = 0
    ADMINEMPLOYEE = 1
    PLAYER = 2
    
 #'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'   
class PicType(str, Enum):  # manually combine str + Enum
    JPG = ".jpg"
    JPEG = ".jpeg"
    PNG = ".png"
    GIF = ".gif"
    BMP = ".bmp"
    WEBP = ".webp"

#'.pdf', '.doc', '.docx', '.txt', '.rtf'
class DocType(str, Enum):  # manually combine str + Enum
    PDF = ".pdf"
    DOC = ".doc"
    DOCX = ".docx"
    TXT = ".txt"
    RTF = ".rtf"

#'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar'
class FileType(str, Enum):  # manually combine str + Enum
    JPG = ".jpg"
    JPEG = ".jpeg"
    PNG = ".png"
    GIF = ".gif"
    PDF = ".pdf"
    DOC = ".doc"
    DOCX = ".docx"
    TXT = ".txt"
    ZIP = ".zip"
    RAR = ".rar"
class MailType(str, Enum):  # manually combine str + Enum
    FORGOTPASSWORD = "forgotpassword.html"
    PLAYERREGISTER = "player_register_otp.html"
    PLAYERONBOARDING = "player_onboard_mail.html"



class LevelType(IntEnum):
    MainGame = 1
    SubGame = 2


class GameTypeName(IntEnum):
    """Game type name enum for different game categories"""
    FREE = 1
    COLORSORTINTUBE = 2

class GameStatus(Enum):
    ACTIVE = 1
    COMPLETED = 2
    FAILED = 3
    ABANDONED = 4

class GameActionType(Enum):
    MOVE = 1
    CLICK = 2
    DRAG = 3
    DROP = 4
    COMPLETE = 5
    FAIL = 6

class PlayerTransactionType(Enum):
    GAME_ENTRY = 1
    REWARD = 2
    WITHDRAWAL = 3
    DEPOSIT = 4

class PlayerTransactionStatus(Enum):
    PENDING = 1
    COMPLETED = 2
    FAILED = 3