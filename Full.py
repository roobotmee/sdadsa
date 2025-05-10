from telethon import TelegramClient, events
from telethon.tl.custom import Button
import re
import asyncio
import logging
import os
import json
import sys
from datetime import datetime, timedelta

logging.basicConfig(
	level=logging.ERROR,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

api_id = 24502935
api_hash = "edfb7c9d2571529865a315e1ae146e34"
target_group_id = -1002355926126

client = None

stats = {
	"forwarded_messages": 0,
	"blocked_messages": 0,
	"last_reset": datetime.now().strftime("%Y-%m-%d")
}

def save_stats():
	with open("stats.json", "w", encoding='utf-8') as f:
		json.dump(stats, f, ensure_ascii=False)

def load_stats():
	global stats
	try:
		if os.path.exists("stats.json"):
			with open("stats.json", "r", encoding='utf-8') as f:
				stats = json.load(f)
	except Exception as e:
		logger.error(f"Statistikani yuklashda xato: {e}")

def safe_log(level, message):
	if level == "error":
		try:
			logger.error(message)
		except Exception:
			pass

trigger_words = [
	# Latin harflarda
	"odam", "kishi", "bor", "kerak", "hozirga", "srochna", "srochni",
	"1 ta", "2 ta", "3 ta", "4 ta", "1ta", "2ta", "3ta", "4ta",
	"bitta", "ikkita", "uchta", "tortta", "ikta", "beshta",
	"1 kishi", "2 kishi", "3 kishi", "4 kishi",
	"dan", "ketaman", "ketadigan", "xozir", "kechga",
	"komplek", "kanpilekt", "kampilek", "kamplek", "kaplek",
	"ayol", "ayollar", "onaxon", "bola", "erkak", "yigit",
	"pochta", "poshta", "bagaj", "yuk", "sumka", "quti", "yuklar",
	"toshkent", "tosh", "fargona", "qoqon", "quqon", "andijon", "namangan",
	"buvayda", "bogdod", "yangiqorgon", "uchkoprik", "rishton", "oltariq",
	"chirchiq", "angren", "ohangaron", "bekobod", "olmaliq", "guliston",
	"yaypan", "beshariq", "pop", "chust", "kosonsoy", "chortoq", "koplonbek",
	"parkent", "keles", "yunusobod", "hasanboy",
	"ga", "ketish", "borish", "ketadi", "boradi", "ketayapman", "borayapman",
	"ertalab", "kechqurun", "soat", "bugun", "ertaga", "tushdan keyin",
	"ming", "som", "pul", "narx", "narxi", "haqi", "tolov",
	"tel", "telefon", "raqam", "nomer", "aloqa", "qongiroq",
	"oldi", "mesta", "joy", "orindiq", "joylar", "orindiqlar",
	"mashina", "avto", "taxi", "taksi", "moshin", "moshina", "avtomobil",
	"yo'lovchi", "yolovchi", "passajir", "mijoz", "kliyent",
	"haydovchi", "shofyor", "shofer",
	
	# Kirill harflarda
	"одам", "киши", "бор", "керак", "ҳозирга", "хозирга", "срочна", "срочни",
	"1 та", "2 та", "3 та", "4 та", "1та", "2та", "3та", "4та",
	"битта", "иккита", "учта", "тўртта", "икта", "бешта",
	"1 киши", "2 киши", "3 киши", "4 киши",
	"дан", "кетаман", "кетадиган", "хозир", "кечга",
	"комплек", "канпилект", "комплект", "капилек", "кампилек", "камлар",
	"аёл", "аёллар", "онахон", "бола", "эркак", "йигит",
	"почта", "пошта", "багаж", "юк", "сумка", "қути", "юклар",
	"тошкент", "тош", "фарғона", "қўқон", "қуқон", "андижон", "наманган",
	"бувайда", "боғдод", "янгиқўрғон", "учкўприк", "риштон", "олтариқ",
	"чирчиқ", "ангрен", "оҳангарон", "бекобод", "олмалиқ", "гулистон",
	"яйпан", "бешариқ", "поп", "чуст", "косонсой", "чортоқ", "коплонбек", "келес", "юнусобод", "хасанбой",
	"га", "кетиш", "бориш", "кетади", "боради", "кетаяпман", "бораяпман",
	"эрталаб", "кечқурун", "соат", "бугун", "эртага", "тушдан кейин",
	"минг", "сўм", "пул", "нарх", "нархи", "ҳақи", "тўлов",
	"тел", "телефон", "рақам", "номер", "алоқа", "қўнғироқ",
	"олди", "места", "жой", "ўриндиқ", "жойлар", "ўриндиқлар",
	"машина", "авто", "такси", "мошин", "мошина", "автомобил",
	"йўловчи", "пассажир", "мижоз", "клиент",
	"ҳайдовчи", "шофёр", "шофер"
]

block_words = [
	"olamiz", "olaman", "olib ketaman", "olib boraman", "yuramiz", "ketamiz", "boramiz", "izlaymiz",
	"оламиз", "оламан", "олиб кетаман", "олиб бораман", "юрамиз", "кетамиз", "борамиз", "излаймиз",
	"pochta olaman", "pochta olamiz", "bagaj olaman", "bagaj olamiz",
	"почта оламан", "почта оламиз", "багаж оламан", "багаж оламиз", "daromad", "ishlash", "orgataman", "тонна",
	"ga olaman", "ga olamiz", "dan olaman", "dan olamiz",
	"га оламан", "га оламиз", "дан оламан", "дан оламиз",
	"odamlarni olaman", "odamlarni olamiz", "одамларни оламан", "одамларни оламиз",
	"yuk olaman", "yuk olamiz", "юк оламан", "юк оламиз",
	"pochta bor", "bagaj bor", "почта бор", "багаж бор",
	"sotiladi", "sotaman", "sotib olaman", "sotib olamiz",
	"сотилади", "сотаман", "сотиб оламан", "сотиб оламиз",
	"reklama", "e'lon", "bot", "kanal", "guruh", "gruppa",
	"реклама", "эълон", "бот", "канал", "гуруҳ", "группа",
	"qidiryapman", "qidiramiz", "izlayapman", "izlaymiz",
	"қидиряпман", "қидирамиз", "излаяпман", "излаймиз",
	"kerak edi", "kerak emas", "sotiladimi", "olasizmi",
	"керак эди", "керак эмас", "сотиладими", "оласизми",
	"qayerda", "qanaqa", "qanday", "qancha", "qachon",
	"қаерда", "қанақа", "қандай", "қанча", "қачон",
	"admin", "administrator", "moderator", "ruxsat", "mumkinmi",
	"админ", "администратор", "модератор", "рухсат", "мумкинми",
	"ish", "ishga", "xizmat", "xodim", "hodim", "vakansiya",
	"иш", "ишга", "хизмат", "ходим", "вакансия",
	"o'qish", "o'qishga", "talaba", "student", "institut", "universitet",
	"ўқиш", "ўқишга", "талаба", "студент", "институт", "университет",
	"topildi", "yo'qoldi", "yo'qotdim", "topolmayapman",
	"топилди", "йўқолди", "йўқотдим", "тополмаяпман",
	"uy", "kvartira", "xona", "ijara", "ijaraga",
	"уй", "квартира", "хона", "ижара", "ижарага",
	"𝐊𝐀𝐌", "𝐎𝐋𝐀𝐌𝐈𝐙",
	"savob", "savobli", "iloji", "aka", "oka", "uka", "raxmat", "rahmat",
	"савоб", "савобли", "илож", "а��а", "ока", "ука", "рахмат", "раҳмат",
	"mikroqarz", "mikro qarz", "kredit", "qarz", "foiz", "foyz", "bank", "onlayn", "chasniy",
	"million", "karta", "pasport", "hujjat", "beriladi", "yillik", "yilga", "mikrokredit",
	"mikrozaym", "zaym", "займ", "кредит", "микрокредит", "микрозайм", "банк", "фоиз", "процент",
	"миллион", "карта", "паспорт", "ҳужжат", "берилади", "йиллик", "йилга", "микроқарз",
	"oldi joy", "oldi joy bor", "oldi joy bush", "oldi o'rindiq", "oldi o'rindiq bor",
	"олди жой", "олди жой бор", "олди жой буш", "олди ўриндиқ", "олди ўриндиқ бор",
	"joy bor", "joy bush", "o'rindiq bor", "o'rindiq bush",
	"жой бор", "жой буш", "ўриндиқ бор", "ўриндиқ буш",
	"tamonlardan", "atrofidan", "тамонлардан", "атрофидан",
	"pustoy", "пустой", "bo'sh", "бўш", "bush", "буш",
	"klient vaqtiga", "клиент вахтига", "клент вахтига", "mijoz vaqtiga", "мижоз вақтига",
	"cobalt bor", "кобалт бор", "nexia bor", "нексия бор", "lacetti bor", "лачетти бор",
	"spark bor", "спарк бор", "matiz bor", "матиз бор", "damas bor", "дамас бор",
	"андижон шахардан тошкентга пустой кобалт бор", "andijon shahardan toshkentga pustoy cobalt bor",
	
	# Yangi qo'shilgan so'zlar
	"kam", "кам", "2ta kam", "2 ta kam", "2та кам", "2 та кам"
]

ignore_words = ["your user id:", "current chat id:"]

spam_words = [
	"ищем", "набор", "удаленную", "работу", "работа", "доход", "смену", "опыт", "обучаем",
	"заработок", "подработка", "вакансия", "вакансии", "зарплата", "оплата",
	"адекватных", "женский", "пол", "школьники", "гибкое", "начало", "мск",
	"писать сюда", "по работе", "пишите", "телеграм", "ссылка",
	
	# Yangi qo'shilgan so'zlar - rus tilidagi spam
	"удалённый", "уdalennый", "WОRК", "DOXOD", "smenu", "raboта", "noчью", "naчиная",
	"берём", "ноvичkov", "obuчаем", "пишиte", "сюda", "регистрация", "тозаси", "whatsapp",
	"халоликни", "фойдаси", "баракали", "иншаллах", "проверка", "запрет", "депорт",
	"не женат", "справка", "не судимост", "трудовой", "договор", "миграционная", "карта",
	"нотариално", "давнрност", "патент", "чек", "перевод", "паспорт", "права", "балничный",
	"лист", "мед книжка", "снилс", "инн", "крг", "ади", "диплом", "кара права", "тех пас",
	"алпинист", "корочка", "сварщик", "удоствирени", "жуда арзон", "нархда", "сифатли",
	"нужен сотрудник", "нашу компанию", "берем без опыта", "оплата", "неделя", "график",
	"удаленный", "связь", "manager_bot", "crypto_arbitbot",
	
	# Qo'shimcha so'zlar - transport xabarlari uchun
	"погрузка", "площадка", "карабулак", "ташкент"
]

direction_pattern = re.compile(
	r'([A-Za-zА-Яа-яЎўҚқҒғҲҳ]+)(?:dan|дан|ДАН|Dan|Дан)\s+([A-Za-zА-Яа-яЎўҚқҒғҲҳ]+)(?:ga|га|ГА|Ga|Га)', re.IGNORECASE)

destination_pattern = re.compile(
	r'\b([A-Za-zА-Яа-яЎўҚқҒғҲҳ]+)(?:ga|га|ГА|Ga|Га)\b', re.IGNORECASE)

origin_pattern = re.compile(
	r'\b([A-Za-zА-Яа-яЎўҚқҒғҲҳ]+)(?:dan|дан|ДАН|Dan|Дан)\b', re.IGNORECASE)

city_from_pattern = re.compile(
	r'([A-Za-zА-Яа-яЎўҚқҒғҲҳ]+)\s+(?:shahar|шахар|шаҳар)(?:dan|дан|ДАН|Dan|Дан)', re.IGNORECASE)

city_to_pattern = re.compile(
	r'([A-Za-zА-Яа-яЎўҚқҒғҲҳ]+)(?:ga|га|ГА|Ga|Га)\s+(?:shahar|шахар|шаҳар)', re.IGNORECASE)

def clean_text(text):
	for char in ".,;:!?-_()[]{}\"'":
		text = text.replace(char, " ")
	
	return re.sub(r'\s+', ' ', text).strip()

def replace_dots_with_spaces(text):
	# Nuqtalarni bo'sh joylar bilan almashtirish
	return text.replace(".", " ")

def check_word_in_text(word, text):
	if word in text:
		return True
	
	words = text.split()
	return word in words

def extract_message_content(text):
	if "✉️ Xabar:" in text:
		message_content = text.split("✉️ Xabar:")[1].strip()
		return message_content
	return text

def extract_user_info(text):
	info = {
		"id": None,
		"name": None,
		"username": None,
		"phone": None,
		"message": None,
		"name_link": None
	}
	
	lines = text.split('\n')
	for i, line in enumerate(lines):
		if line.startswith("ID:") or line.startswith("🔹 ID:"):
			info["id"] = line.split(":", 1)[1].strip()
		elif line.startswith("🔹 Ism:"):
			name_part = line.split(":", 1)[1].strip()
			
			href_match = re.search(r'<a href=[\'"]([^\'"]+)[\'"]>([^<]+)</a>', name_part)
			if href_match:
				info["name_link"] = href_match.group(1)
				info["name"] = href_match.group(2)
			else:
				info["name"] = name_part
		elif line.startswith("🔹 Username:"):
			username_text = line.split(":", 1)[1].strip()
			if username_text.startswith("@"):
				info["username"] = username_text
			elif "Profilga o'tish" not in username_text:
				info["username"] = username_text
		elif line.startswith("🔹 Telefon Raqami:"):
			phone_text = line.split(":", 1)[1].strip()
			if phone_text != "Taminlanmagan" and phone_text != "Ta'minlanmagan":
				info["phone"] = phone_text
		elif "✉️ Xabar:" in line:
			message_start_index = i
			message_parts = []
			for j in range(message_start_index, len(lines)):
				if j == message_start_index:
					if ":" in lines[j]:
						message_parts.append(lines[j].split(":", 1)[1].strip())
					else:
						message_parts.append(lines[j].strip())
				else:
					message_parts.append(lines[j].strip())
			info["message"] = "\n".join(message_parts)
			break
	
	return info

def is_loan_message(text):
	loan_keywords = [
		"mikroqarz", "mikro qarz", "kredit", "qarz", "foiz", "foyz", "bank", "chasniy",
		"million", "karta", "pasport", "hujjat", "beriladi", "yillik", "yilga", "mikrokredit",
		"mikrozaym", "zaym", "займ", "кредит", "микрокредит", "микрозайм", "банк", "фоиз", "процент",
		"миллион", "карта", "паспорт", "ҳужжат", "берилади", "йиллик", "йилга", "микроқарз"
	]
	
	text_lower = text.lower()
	
	loan_word_count = 0
	for word in loan_keywords:
		if word in text_lower:
			loan_word_count += 1
	
	return loan_word_count >= 3

def is_short_or_general_message(text):
	text_lower = text.lower()
	
	has_direction = bool(direction_pattern.search(text_lower))
	has_destination = bool(destination_pattern.search(text_lower))
	has_origin = bool(origin_pattern.search(text_lower))
	has_city_from = bool(city_from_pattern.search(text_lower))
	has_city_to = bool(city_to_pattern.search(text_lower))
	
	if has_direction or has_destination or has_origin or has_city_from or has_city_to:
		return False
	
	if len(text_lower.split()) < 5:
		return True
	
	emoji_count = sum(1 for char in text_lower if ord(char) > 127000)
	if emoji_count > 2 and len(text_lower.split()) < 10:
		return True
	
	general_response_words = [
		"ha", "yo'q", "xa", "yoq", "ok", "xop", "xo'p", "mayli", "bo'ldi", "boldi",
		"raxmat", "rahmat", "savob", "iloji", "kerak", "керак", "ҳа", "йўқ", "ха", "йоқ",
		"хоп", "хўп", "майли", "бўлди", "болди", "рахмат", "раҳмат", "савоб", "илож"
	]
	
	words = text_lower.split()
	general_word_count = sum(1 for word in words if word in general_response_words)
	
	if general_word_count > 0 and len(words) < 8:
		return True
	
	if not (has_direction or has_destination or has_origin or has_city_from or has_city_to) and len(words) < 8:
		return True
	
	return False

def extract_phone_from_message(text):
	phone_pattern = re.compile(
		r'(?:tel|тел|телефон|raqam|номер|nomer)[\s:]*(\+?\d{9,12}|\d{2,3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})',
		re.IGNORECASE)
	phone_match = phone_pattern.search(text)
	if phone_match:
		return phone_match.group(1).strip()
	
	digits_only_pattern = re.compile(r'\b\+?\d{9,12}\b')
	digits_match = digits_only_pattern.search(text)
	if digits_match:
		return digits_match.group(0).strip()
	
	return None

def extract_direction_info(text):
	text_lower = text.lower()
	
	direction_match = direction_pattern.search(text_lower)
	if direction_match:
		return f"{direction_match.group(1)} → {direction_match.group(2)}"
	
	destination_match = destination_pattern.search(text_lower)
	if destination_match:
		return f"? → {destination_match.group(1)}"
	
	origin_match = origin_pattern.search(text_lower)
	if origin_match:
		return f"{origin_match.group(1)} → ?"
	
	city_from_match = city_from_pattern.search(text_lower)
	if city_from_match:
		return f"{city_from_match.group(1)} → ?"
	
	city_to_match = city_to_pattern.search(text_lower)
	if city_to_match:
		return f"? → {city_to_match.group(1)}"
	
	return "Aniqlanmadi"

def is_driver_offering_service(text):
	text_lower = text.lower()
	
	driver_keywords = [
		"olaman", "olib ketaman", "olib boraman", "оламан", "олиб кетаман", "олиб бораман",
		"pochta olaman", "pochta olamiz", "bagaj olaman", "bagaj olamiz",
		"почта оламан", "почта оламиз", "багаж оламан", "багаж оламиз",
		"ga olaman", "ga olamiz", "dan olaman", "dan olamiz",
		"га оламан", "га оламиз", "дан оламан", "дан оламиз"
	]
	
	for keyword in driver_keywords:
		if keyword in text_lower:
			return True
	
	if ("pochta" in text_lower or "почта" in text_lower) and ("olaman" in text_lower or "оламан" in text_lower):
		return True
	
	if ("bagaj" in text_lower or "багаж" in text_lower) and ("olaman" in text_lower or "оламан" in text_lower):
		return True
	
	if ("yuk" in text_lower or "юк" in text_lower) and ("olaman" in text_lower or "оламан" in text_lower):
		return True
	
	return False

def is_driver_message(text):
	text_lower = text.lower()
	
	patterns = [
		r'олди\s+жой\s+буш',
		r'oldi\s+joy\s+bush',
		r'олди\s+ўриндиқ\s+буш',
		r'oldi\s+o\'rindiq\s+bush',
		r'багаж\s+бор',
		r'bagaj\s+bor',
		r'почта\s+бор',
		r'pochta\s+bor',
		r'тамонлардан',
		r'tamonlardan',
		r'атрофидан',
		r'atrofidan',
		r'пустой\s+кобалт\s+бор',
		r'pustoy\s+cobalt\s+bor',
		r'клент\s+вахтига',
		r'klient\s+vaqtiga'
	]
	
	for pattern in patterns:
		if re.search(pattern, text_lower, re.IGNORECASE):
			return True
	
	if ("oldi joy" in text_lower or "олди жой" in text_lower) and ("bor" in text_lower or "бор" in text_lower):
		return True
	
	if ("bagaj" in text_lower or "багаж" in text_lower) and ("bor" in text_lower or "бор" in text_lower):
		return True
	
	if ("pochta" in text_lower or "почта" in text_lower) and ("bor" in text_lower or "бор" in text_lower):
		return True
	
	if ("pustoy" in text_lower or "пустой" in text_lower) and ("cobalt" in text_lower or "кобалт" in text_lower):
		return True
	
	if "клент вахтига" in text_lower or "klient vaqtiga" in text_lower:
		return True
	
	return False

def is_russian_spam(text):
	text_lower = text.lower()
	
	# Rus tilidagi xabarni aniqlash
	russian_chars = sum(1 for char in text_lower if 'а' <= char <= 'я')
	if len(text_lower) > 0 and russian_chars / len(text_lower) > 0.3:
		# Rus tilidagi spam so'zlarni tekshirish
		spam_word_count = 0
		for word in spam_words:
			if word.lower() in text_lower:
				spam_word_count += 1
				if spam_word_count >= 2:
					return True
	
	# Telefon raqami formatini tekshirish
	phone_patterns = [
		r'\+7\d{10}',  # +7XXXXXXXXXX
		r'8\d{10}',  # 8XXXXXXXXXX
		r'\+\d{1,3}\d{9,10}'  # Xalqaro format
	]
	
	for pattern in phone_patterns:
		if re.search(pattern, text_lower):
			return True
	
	# Telegram username'larni tekshirish
	if "@" in text_lower and any(word in text_lower for word in ["пишите", "писать", "связь", "контакт"]):
		return True
	
	return False

def has_kam_word(text):
	text_lower = text.lower()
	words = text_lower.split()
	
	# "kam" so'zini alohida so'z sifatida tekshirish
	if "kam" in words or "кам" in words:
		return True
	
	# "kam" so'zi bilan bog'liq iboralarni tekshirish
	kam_patterns = [
		r'\d+\s*ta\s*kam',
		r'\d+\s*та\s*кам',
		r'kam\s*\d+\s*ta',
		r'кам\s*\d+\s*та'
	]
	
	for pattern in kam_patterns:
		if re.search(pattern, text_lower):
			return True
	
	return False

def is_document_spam(text):
	text_lower = text.lower()
	
	document_keywords = [
		"регистрация", "справка", "трудовой договор", "миграционная карта", "патент",
		"перевод паспорт", "перевод права", "балничный лист", "мед книжка", "снилс",
		"инн", "диплом", "права", "тех пас", "удоствирени", "корочка", "арзон нархда"
	]
	
	document_count = 0
	for keyword in document_keywords:
		if keyword in text_lower:
			document_count += 1
			if document_count >= 3:
				return True
	
	# Tekshirish belgisi (✅) ko'p bo'lsa
	if text_lower.count("✅") >= 3:
		return True
	
	return False

def has_excessive_symbols(text):
	# Haddan tashqari undov belgilari yoki boshqa belgilar borligini tekshirish
	exclamation_count = text.count('!')
	if exclamation_count > 10:
		return True
	
	# Bir xil belgilar ketma-ketligini tekshirish
	for symbol in ['!', '?', '*', '#', '=', '+', '-', '‼️']:
		if symbol * 5 in text:
			return True
	
	# Emoji ketma-ketligini tekshirish
	emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
	emojis = emoji_pattern.findall(text)
	if len(emojis) > 10:
		return True
	
	# Bir xil emoji ketma-ketligini tekshirish
	if emojis:
		emoji_counts = {}
		for emoji in emojis:
			emoji_counts[emoji] = emoji_counts.get(emoji, 0) + 1
			if emoji_counts[emoji] >= 5:
				return True
	
	return False

def has_trigger_word_and_bor_or_ketish_kerak(text):
	text_lower = text.lower()
	words = text_lower.split()
	
	# "bor" so'zi bor-yo'qligini tekshirish
	has_bor = "bor" in words or "бор" in words
	
	# "ketish kerak" yoki "ketishim kerak" iboralari bor-yo'qligini tekshirish
	has_ketish_kerak = ("ketish kerak" in text_lower or "ketishim kerak" in text_lower or
	                    "кетиш керак" in text_lower or "кетишим керак" in text_lower or
	                    "borish kerak" in text_lower or "borishim kerak" in text_lower or
	                    "бориш керак" in text_lower or "боришим керак" in text_lower)
	
	# Agar "bor" yoki "ketish kerak" iboralari bo'lmasa, false qaytarish
	if not (has_bor or has_ketish_kerak):
		return False
	
	# Trigger so'zlardan kamida bittasi bor-yo'qligini tekshirish
	for word in trigger_words:
		if word.lower() in text_lower:
			return True
	
	return False

def has_any_block_word(text):
	text_lower = text.lower()
	cleaned_text = clean_text(text_lower)
	words = cleaned_text.split()
	
	for word in block_words:
		if word.lower() in words:
			return True
	
	return False

async def process_message(event):
	try:
		if event.out:
			return
		
		try:
			sender = await event.get_sender()
			if sender and hasattr(sender, 'bot') and sender.bot:
				return
		except Exception:
			sender = None
		
		original_full_text = getattr(event.message, "text", "").strip()
		if not original_full_text:
			return
		
		current_date = datetime.now().strftime("%Y-%m-%d")
		if stats["last_reset"] != current_date:
			stats["forwarded_messages"] = 0
			stats["blocked_messages"] = 0
			stats["last_reset"] = current_date
			save_stats()
		
		is_private_chat = event.chat_id > 0
		
		is_public_group = False
		group_username = None
		
		if not is_private_chat:
			try:
				chat = await event.get_chat()
				if hasattr(chat, "username") and chat.username:
					group_username = chat.username
					is_public_group = True
			except Exception as e:
				safe_log("error", f"Guruh ma'lumotlarini olishda xato: {e}")
		
		user_username = None
		user_name_link = None
		
		# Xabar formatini tekshirish
		if "ID:" in original_full_text or "🔹 ID:" in original_full_text:
			user_info = extract_user_info(original_full_text)
			
			# Xabar bo'sh bo'lsa ham, foydalanuvchi ma'lumotlarini olish
			original_text = user_info["message"] if user_info["message"] else ""
			user_id = user_info["id"]
			user_name = user_info["name"]
			user_phone = user_info["phone"]
			user_username = user_info["username"]
			user_name_link = user_info["name_link"]
			
			user_link = f"tg://user?id={user_id}" if user_id else None
			
			# Agar xabar bo'sh bo'lsa va ID formati bo'lsa, filtrlashsiz yuborish
			is_empty_message_with_id = "✉️ Xabar:" in original_full_text and not original_text
			
			if is_empty_message_with_id:
				# Xabarni formatlash va yuborish
				formatted_message = f"👋 Yangi buyurtma \n"
				
				if is_public_group and group_username:
					formatted_message += f"👥 <b>Manba:</b> <a href='https://t.me/{group_username}'>@VipTaxisBot</a>\n"
				elif is_private_chat and user_id:
					formatted_message += f"👥 <b>Manba:</b> <a href='tg://user?id={user_id}'>@VipTaxisBot</a>\n"
				else:
					formatted_message += f"👥 <b>Manba:</b> @VipTaxisBot\n"
				
				if user_id:
					formatted_message += f"👤 <b>Murojaat:</b> <a href='tg://user?id={user_id}'>...</a>\n"
				elif user_username and user_username.startswith("@"):
					formatted_message += f"👤 <b>Murojaat:</b> <a href='https://t.me/{user_username[1:]}'>...</a>\n"
				else:
					formatted_message += f"👤 <b>Murojaat:</b> ...\n"
				
				# User ma'lumotlari - username bilan
				if user_username and user_username.startswith("@"):
					formatted_message += f"👤 <b>User:</b> {user_username}\n"
				else:
					formatted_message += f"👤 <b>User:</b> None\n"
				
				if user_phone and user_phone != "Telefon raqami yo'q":
					formatted_message += f"📞 <b>Telefon</b> {user_phone}\n"
				else:
					formatted_message += f"📞 <b>Telefon</b> Telefon raqami yo'q\n"
				
				formatted_message += f"🚕 <b>Yo'nalish:</b> Aniqlanmadi\n\n"
				
				# Asl xabarni yuborish (nuqtalarni almashtirmasdan)
				formatted_message += f" <b>======✉️Xabar======</b>\n\n {original_text}\n\n"
				
				formatted_message += f"🤲 Oq yo'l, Biz test rejimida ishlayabmiz Muammo bolsa buni xal qilamiz."
				
				try:
					await client.send_message(
						target_group_id,
						formatted_message,
						parse_mode='html'
					)
					
					stats["forwarded_messages"] += 1
					save_stats()
					safe_log("error", f"Bo'sh xabar yuborildi: ID {user_id}")
				except Exception as e:
					safe_log("error", f"Xabar yuborishda xato: {e}")
				
				return
		else:
			original_text = extract_message_content(original_full_text)
			user_id = getattr(sender, 'id', 0) if sender else 0
			user_name = getattr(sender, 'first_name', None) if sender else None
			user_username = getattr(sender, 'username', None) if sender else None
			if user_username:
				user_username = f"@{user_username}"
			user_link = f"tg://user?id={user_id}" if user_id > 0 else None
			
			if sender and hasattr(sender, 'phone') and sender.phone:
				user_phone = f"+{sender.phone}"
			else:
				user_phone = None
		
		# Nuqtalarni bo'sh joylar bilan almashtirish
		original_text_cleaned = replace_dots_with_spaces(original_text)
		
		text_lower = original_text_cleaned.lower()
		
		# Yangi filtrlash qoidasi: kamida bitta trigger so'z va "bor" so'zi yoki "ketish kerak" iborasi bo'lishi kerak
		# va block_words ro'yxatidagi so'zlar bo'lmasligi kerak
		if not has_trigger_word_and_bor_or_ketish_kerak(text_lower):
			stats["blocked_messages"] += 1
			save_stats()
			safe_log("error",
			         f"Xabar bloklandi (trigger so'z yoki 'bor'/'ketish kerak' so'zi yo'q): {original_text[:50]}...")
			return
		
		# Block so'zlarni tekshirish
		if has_any_block_word(text_lower):
			stats["blocked_messages"] += 1
			save_stats()
			safe_log("error", f"Xabar bloklandi (block so'z topildi): {original_text[:50]}...")
			return
		
		# "kam" so'zini tekshirish
		if has_kam_word(text_lower):
			stats["blocked_messages"] += 1
			save_stats()
			safe_log("error", f"Xabar bloklandi (kam so'zi): {original_text[:50]}...")
			return
		
		# Haddan tashqari belgilar borligini tekshirish
		if has_excessive_symbols(original_text):
			stats["blocked_messages"] += 1
			save_stats()
			safe_log("error", f"Xabar bloklandi (haddan tashqari belgilar): {original_text[:50]}...")
			return
		
		# Rus tilidagi spam xabarlarni tekshirish
		if is_russian_spam(text_lower):
			stats["blocked_messages"] += 1
			save_stats()
			safe_log("error", f"Xabar bloklandi (rus tilidagi spam): {original_text[:50]}...")
			return
		
		# Hujjat xizmatlari haqidagi spam xabarlarni tekshirish
		if is_document_spam(text_lower):
			stats["blocked_messages"] += 1
			save_stats()
			safe_log("error", f"Xabar bloklandi (hujjat spam): {original_text[:50]}...")
			return
		
		if is_driver_message(text_lower) or is_driver_offering_service(text_lower):
			stats["blocked_messages"] += 1
			save_stats()
			safe_log("error", f"Xabar bloklandi (haydovchi xabari): {original_text[:50]}...")
			return
		
		if "пустой кобалт бор" in text_lower or "pustoy cobalt bor" in text_lower:
			stats["blocked_messages"] += 1
			save_stats()
			return
		
		if "клент вахтига" in text_lower or "klient vaqtiga" in text_lower:
			stats["blocked_messages"] += 1
			save_stats()
			return
		
		if is_loan_message(text_lower):
			stats["blocked_messages"] += 1
			save_stats()
			return
		
		# Spam so'zlarni tekshirish
		spam_word_count = 0
		for word in spam_words:
			if word.lower() in text_lower:
				spam_word_count += 1
				if spam_word_count >= 2:
					stats["blocked_messages"] += 1
					save_stats()
					safe_log("error", f"Xabar bloklandi (spam so'zlar): {original_text[:50]}...")
					return
		
		# Maxsus buyruqlarni tekshirish
		if text_lower == "/del":
			if event.chat_id == target_group_id:
				async for message in client.iter_messages(target_group_id):
					await client.delete_messages(target_group_id, message.id)
			return
		
		if text_lower == "/stats":
			if event.chat_id == target_group_id:
				stats_message = (
					f"📊 Bugungi statistika ({stats['last_reset']}):\n"
					f"✅ Yuborilgan xabarlar: {stats['forwarded_messages']}\n"
					f"❌ Bloklangan xabarlar: {stats['blocked_messages']}"
				)
				await client.send_message(event.chat_id, stats_message)
			return
		
		if any(word in text_lower for word in ignore_words):
			return
		
		# Chat ma'lumotlarini olish
		try:
			if is_private_chat:
				chat_title = f"Shaxsiy chat: {user_name}" if user_name else "Shaxsiy chat"
				chat_username = f"tg://user?id={event.chat_id}"
			else:
				chat = await event.get_chat()
				chat_title = getattr(chat, "title", "Guruh nomi yo'q")
				if is_public_group and group_username:
					chat_username = f"https://t.me/{group_username}"
				else:
					chat_username = "Guruh linki yo'q"
		except Exception as e:
			safe_log("error", f"Chat ma'lumotlarini olishda xato: {e}")
			chat_title = "Guruh nomi yo'q"
			chat_username = "Guruh linki yo'q"
		
		# Telefon raqamini olish
		if not user_phone:
			extracted_phone = extract_phone_from_message(original_text_cleaned)
			if extracted_phone:
				user_phone = extracted_phone
			else:
				user_phone = "Telefon raqami yo'q"
		
		# Yo'nalish ma'lumotlarini olish
		direction = extract_direction_info(text_lower)
		
		# Xabarni formatlash va yuborish
		formatted_message = f"👋 Yangi buyurtma \n"
		
		if is_public_group and group_username:
			formatted_message += f"👥 <b>Manba:</b> <a href='https://t.me/{group_username}'>@VipTaxisBot</a>\n"
		elif is_private_chat and user_id:
			formatted_message += f"👥 <b>Manba:</b> <a href='tg://user?id={user_id}'>@VipTaxisBot</a>\n"
		else:
			formatted_message += f"👥 <b>Manba:</b> @VipTaxisBot\n"
		
		if user_id:
			formatted_message += f"👤 <b>Murojaat:</b> <a href='tg://user?id={user_id}'>...</a>\n"
		elif user_username and user_username.startswith("@"):
			formatted_message += f"👤 <b>Murojaat:</b> <a href='https://t.me/{user_username[1:]}'>...</a>\n"
		else:
			formatted_message += f"👤 <b>Murojaat:</b> ...\n"
		
		# User ma'lumotlari - username bilan
		if user_username and user_username.startswith("@"):
			formatted_message += f"👤 <b>User:</b> {user_username}\n"
		else:
			formatted_message += f"👤 <b>User:</b> None\n"
		
		if user_phone and user_phone != "Telefon raqami yo'q":
			formatted_message += f"📞 <b>Telefon</b> {user_phone}\n"
		else:
			extracted_phone = extract_phone_from_message(original_text_cleaned)
			if extracted_phone:
				formatted_message += f"📞 <b>Telefon</b> {extracted_phone}\n"
			else:
				formatted_message += f"📞 <b>Telefon</b> Telefon raqami yo'q\n"
		
		formatted_message += f"🚕 <b>Yo'nalish:</b> {direction}\n\n"
		
		# Asl xabarni yuborish (nuqtalarni almashtirmasdan)
		formatted_message += f" <b>======✉️Xabar======</b>\n\n {original_text}\n\n"
		
		formatted_message += f"🤲 Oq yo'l, Biz test rejimida ishlayabmiz Muammo bolsa buni xal qilamiz."
		
		try:
			await client.send_message(
				target_group_id,
				formatted_message,
				parse_mode='html'
			)
			
			stats["forwarded_messages"] += 1
			save_stats()
			safe_log("error", f"Xabar yuborildi: {original_text[:50]}...")
		except Exception as e:
			safe_log("error", f"Xabar yuborishda xato: {e}")
	except Exception as e:
		safe_log("error", f"Xabarni qayta ishlashda xato: {e}")

async def main():
	global client
	
	try:
		load_stats()
		
		print("Telefon raqamingizni kiriting (+998xxxxxxxxx formatida):")
		phone_number = input().strip()
		
		if not phone_number.startswith("+"):
			phone_number = "+" + phone_number
		
		print(f"Kiritilgan telefon raqami: {phone_number}")
		
		client = TelegramClient("azamjon_vipe", api_id, api_hash)
		
		await client.start(phone_number)
		
		client.add_event_handler(process_message, events.NewMessage)
		
		print("Userbot ishga tushdi...")
		print(f"Telegram serveriga ulanildi: {phone_number}")
		
		try:
			dialogs = await client.get_dialogs()
			groups = [d for d in dialogs if d.is_group]
			
			print(f"Bot {len(groups)} ta guruhda mavjud")
			print("Guruhlar ro'yxati:")
			for i, dialog in enumerate(groups[:10], 1):
				print(f"{i}. {dialog.title} (ID: {dialog.id})")
		except Exception as e:
			safe_log("error", f"Guruhlarni ko'rsatishda xato: {e}")
		
		print("\nBot xabarlarni kuzatishni boshladi...")
		print("Botni to'xtatish uchun Ctrl+C bosing")
		
		await client.run_until_disconnected()
	
	except Exception as e:
		safe_log("error", f"Botni ishga tushirishda xato: {e}")
	finally:
		if client:
			await client.disconnect()

if __name__ == "__main__":
	print("Bot ishga tushmoqda...")
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		print("\nBot to'xtatildi")
	except Exception as e:
		print(f"Xato yuz berdi: {e}")