# =======================================================================
# CELLULE PRINCIPALE DU BOT (VERSION STABLE ET CORRIGÉE)
# =======================================================================

# =======================================================================
# SECTION 1 : IMPORTS
# =======================================================================
from flask import Flask
import threading
import logging
import os
import re
import pypandoc
import datetime
import locale
import openai
from openai import OpenAI

# Imports de la librairie python-telegram-bot
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
)
# =======================================================================
# FIN DE LA SECTION 1
# =======================================================================


# =======================================================================
# SECTION 2 : CONFIGURATION ET CLÉS API
# =======================================================================
# On charge les clés depuis les variables d'environnement.
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("ERREUR : Clés API manquantes. Vérifiez les variables d'environnement.")

client = OpenAI(api_key=OPENAI_API_KEY)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
# =======================================================================
# FIN DE LA SECTION 2
# =======================================================================


# =======================================================================
# SECTION 2.5 : DICTIONNAIRE DE TRADUCTIONS
# =======================================================================
TITLES = {
    'fr': {
        "FICHE_DE_LECON": "FICHE DE LEÇON APC", "OBJECTIFS": "OBJECTIFS PÉDAGOGIQUES",
        "SITUATION_PROBLEME": "SITUATION PROBLÈME", "DEROULEMENT": "DÉROULEMENT DE LA LEÇON",
        "INTRODUCTION": "Introduction (5 min)", "ACTIVITE_1": "Activité 1: Découverte (10 min)",
        "ACTIVITE_2": "Activité 2: Conceptualisation et TRACE ÉCRITE (20 min)",
        "TRACE_ECRITE": "Trace Écrite", "ACTIVITE_3": "Activité 3: Application (10 min)",
        "DEVOIRS": "DEVOIRS", "JEU_BILINGUE": "JEU BILINGUE / BILINGUAL GAME",
        "HEADER_MATIERE": "Matière", "HEADER_CLASSE": "Classe", "HEADER_DUREE": "Durée",
        "HEADER_LECON": "Leçon du jour", "PDF_TITLE": "Fiche de Leçon", "PDF_AUTHOR": "Assistant Pédagogique MINESEC IA"
    },
    'en': {
        "FICHE_DE_LECON": "CBA LESSON PLAN", "OBJECTIFS": "LEARNING OBJECTIVES",
        "SITUATION_PROBLEME": "PROBLEM SITUATION", "DEROULEMENT": "LESSON PLAN",
        "INTRODUCTION": "Introduction (5 min)", "ACTIVITE_1": "Activity 1: Discovery (10 min)",
        "ACTIVITE_2": "Activity 2: Conceptualization and WRITTEN RECORD (20 min)",
        "TRACE_ECRITE": "Written Record", "ACTIVITE_3": "Activity 3: Application (10 min)",
        "DEVOIRS": "HOMEWORK", "JEU_BILINGUE": "BILINGUAL GAME / JEU BILINGUE",
        "HEADER_MATIERE": "Subject", "HEADER_CLASSE": "Class", "HEADER_DUREE": "Duration",
        "HEADER_LECON": "Lesson of the Day", "PDF_TITLE": "Lesson Plan", "PDF_AUTHOR": "MINESEC IA Pedagogical Assistant"
    },
    # Ajoutez d'autres langues ici...
}
# =======================================================================
# FIN DE LA SECTION 2.5
# =======================================================================


# =======================================================================
# SECTION 2.6 : LISTES D'OPTIONS POUR LES MENUS
# =======================================================================
AUTRE_OPTION_FR = "✍️ Autre (préciser)"
AUTRE_OPTION_EN = "✍️ Other (specify)"
SUBSYSTEME_FR = ['Enseignement Secondaire Général (ESG)', 'Enseignement Secondaire Technique (EST)']
SUBSYSTEME_EN = ['General Education', 'Technical Education']
CLASSES = {
    'fr': {'esg': ['6ème', '5ème', '4ème', '3ème', 'Seconde', 'Première', 'Terminale']},
    'en': {'esg': ['Form 1', 'Form 2', 'Form 3', 'Form 4', 'Form 5', 'Lower Sixth', 'Upper Sixth']}
}
MATIERES = {
    'fr': {'esg': ['Mathématiques', 'Physique', 'Chimie', 'SVT', 'Français', 'Histoire', 'Géographie', 'Philosophie', 'Anglais']},
    'en': {'esg': ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'History', 'Geography', 'Computer Science', 'English', 'French']}
}
LANGUES_CONTENU = ['Français', 'English', 'Deutsch', 'Español', 'Italiano', '中文 (Chinois)', 'العربية (Arabe)']
# =======================================================================
# FIN DE LA SECTION 2.6
# =======================================================================


# =======================================================================
# SECTION 3 : LE "PROMPT MAÎTRE"
# =======================================================================
PROMPT_UNIVERSAL = """Tu es MINESEC IA, un expert en ingénierie pédagogique pour le Cameroun.
**RÈGLES ABSOLUES DE FORMATAGE :**
1.  **Format Principal :** Tu DOIS utiliser le formatage **Markdown**.
2.  **Gras :** Utilise `**Texte en gras**` pour TOUS les titres.
3.  **Italique :** Utilise `*Texte en italique*` pour les instructions.
4.  **Listes :** Utilise TOUJOURS un tiret `-` pour les listes.
5.  **INTERDICTION FORMELLE :** N'utilise JAMAIS de balises HTML (`<b>`, `<i>`) ni de blocs de code (` ``` `).
6.  **IMPORTANT :** Les titres de section (comme `**{objectifs}**`) ne doivent JAMAIS commencer par une puce de liste.
**LANGUE DE RÉDACTION FINALE :** {langue_contenu}
**DONNÉES DE LA LEÇON :**
- Classe: {classe}
- Matière: {module}
- Titre: {lecon}
- Extrait du Syllabus: "{syllabus}"
---
**GÉNÈRE MAINTENANT la fiche de leçon en suivant EXACTEMENT cette structure et ces titres :**
**{fiche_de_lecon}**
**{header_matiere}:** {module}
**{header_classe}:** {classe}
**{header_duree}:** 50 minutes
**{header_lecon}:** {lecon}

**{objectifs}**
*(Formule ici 2-3 objectifs clairs et mesurables en utilisant des listes avec des tirets "-". )*

**{situation_probleme}**
*(Rédige ici un scénario détaillé et contextualisé au Cameroun avec Contexte, Tâche, et Consignes.)*

**{deroulement}**
**{introduction}:**
*- Rédige une ou plusieurs questions de rappel des pré-requis.*

**{activite_1}:**
*- Rédige le contenu d'une activité de découverte.*

**{activite_2}:**
- **{trace_ecrite}:** *(Rédige ici le cours complet et détaillé (minimum 400 mots) dans le style d'un cours MINESEC.)*

**{activite_3}:**
*- Rédige un exercice d'application complet à faire en classe, suivi de son corrigé détaillé.*

**{devoirs}**
*(Rédige 2 exercices complets pour la maison.)*

<bilingual_data>
<!--
INSTRUCTIONS : Génère ici 5 lignes de données pour le tableau bilingue. Format: Mot;Traduction
- Si la langue de la leçon est 'Français' -> Format: MotEnFrançais;TraductionEnAnglais
- Si la langue de la leçon est 'Anglais' -> Format: MotEnAnglais;TraductionEnFrançais
-->
</bilingual_data>
"""
# =======================================================================
# FIN DE LA SECTION 3
# =======================================================================


# =======================================================================
# SECTION 4 : FONCTIONS UTILITAIRES
# =======================================================================
def build_keyboard(items, other_option_label, items_per_row=2):
    keyboard = [items[i:i + items_per_row] for i in range(0, len(items), items_per_row)]
    if other_option_label: keyboard.append([other_option_label])
    return keyboard

def call_openai_api(prompt):
    try:
        logger.info("Appel à l'API OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=3500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API OpenAI: {e}")
        return f"Désolé, une erreur est survenue. Détails: {e}"

def create_pdf_with_pandoc(text, filename="document.pdf", lang_contenu_code='fr'):
    try:
        logger.info(f"Création du PDF avec Pandoc : {filename}")
        if "<bilingual_data>" in text:
            main_markdown_raw, bilingual_data_raw = text.split("<bilingual_data>")[:2]
            bilingual_data_raw = bilingual_data_raw.split("</bilingual_data>")[0]
        else:
            main_markdown_raw, bilingual_data_raw = text, ""
        
        main_markdown_final = re.sub(r'<!--.*?-->', '', main_markdown_raw, flags=re.DOTALL).strip()
        markdown_table = ""
        if bilingual_data_raw:
            bilingual_content = re.sub(r'<!--.*?-->', '', bilingual_data_raw, flags=re.DOTALL).strip()
            lines = [line.strip() for line in bilingual_content.split('\n') if line.strip() and ';' in line]
            if lines:
                table_title = TITLES.get(lang_contenu_code, TITLES['fr'])['JEU_BILINGUE']
                markdown_table += f"\n\n**{table_title}**\n\n"
                headers = ['N°', 'Français', 'English'] if lang_contenu_code == 'fr' else ['N°', 'English', 'Français']
                markdown_table += f"| {headers[0]} | {headers[1]} | {headers[2]} |\n|:---:|:---|:---|\n"
                for i, line in enumerate(lines):
                    parts = [p.strip() for p in line.split(';')]
                    if len(parts) == 2: markdown_table += f"| {i+1} | {parts[0]} | {parts[1]} |\n"
        
        final_markdown_doc = main_markdown_final + markdown_table
        selected_pdf_titles = TITLES.get(lang_contenu_code, TITLES['fr'])
        
        try:
            locale.setlocale(locale.LC_TIME, f'{lang_contenu_code}_{lang_contenu_code.upper()}.UTF-8' if lang_contenu_code != 'zh' else 'en_US.UTF-8')
        except locale.Error:
            locale.setlocale(locale.LC_TIME, '')
            
        formatted_date = datetime.date.today().strftime('%d %B %Y')
        yaml_header = f"""---
title: "{selected_pdf_titles.get('PDF_TITLE', 'Fiche de Leçon')}"
author: "{selected_pdf_titles.get('PDF_AUTHOR', 'MINESEC IA')}"
date: "{formatted_date}"
lang: "{lang_contenu_code}"
geometry: "margin=1in"
mainfont: "Liberation Serif"
header-includes:
- \\usepackage{{amsmath}}
- \\usepackage{{amssymb}}
---"""
        document_source = yaml_header + "\n" + final_markdown_doc
        pypandoc.convert_text(document_source, 'pdf', format='markdown', outputfile=filename, extra_args=['--pdf-engine=xelatex'])
        logger.info(f"PDF '{filename}' créé avec succès !")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du PDF : {e}")
        if 'document_source' in locals(): logger.error(f"Source Markdown problématique (extrait) : {document_source[:1000]}")
        return False

def run_flask_app():
    app = Flask(__name__)
    @app.route('/health')
    def health_check(): return "OK", 200
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
# =======================================================================
# FIN DE LA SECTION 4
# =======================================================================


# =======================================================================
# SECTION 5 : LOGIQUE DE CONVERSATION
# =======================================================================
(SELECT_LANG, SELECT_OPTION, CHOOSE_SUBSYSTEM, CHOOSE_CLASSE, MANUAL_CLASSE,
 CHOOSE_MATIERE, MANUAL_MATIERE, MANUAL_LECON, CHOOSE_LANGUE_CONTENU,
 MANUAL_LANGUE, GET_SYLLABUS) = range(11)

# --- Fonctions de la conversation ---
def start(update: Update, context: CallbackContext) -> int:
    keyboard = [['Français 🇫🇷'], ['English 🇬🇧']]
    update.message.reply_text("Bonjour! Je suis MINESEC IA. Choisissez votre langue.\n\nHello! I am MINESEC IA. Please choose your language.",
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return SELECT_LANG

def select_lang(update: Update, context: CallbackContext) -> int:
    lang = 'en' if 'English' in update.message.text else 'fr'
    context.user_data['lang'] = lang
    options = [['Préparer une leçon' if lang == 'fr' else 'Prepare a lesson'], ['Produire une évaluation (bientôt)' if lang == 'fr' else 'Create an assessment (soon)']]
    reply_text = "Langue sélectionnée : Français. Que souhaitez-vous faire ?" if lang == 'fr' else "Language selected: English. What would you like to do?"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(options, one_time_keyboard=True))
    return SELECT_OPTION

def ask_for_subsystem(update: Update, context: CallbackContext) -> int:
    context.user_data['lesson_info'] = {}
    lang = context.user_data.get('lang', 'fr')
    subsystem_list = SUBSYSTEME_FR if lang == 'fr' else SUBSYSTEME_EN
    keyboard = [[s] for s in subsystem_list]
    reply_text = "Veuillez sélectionner le sous-système d'enseignement :" if lang == 'fr' else "Please select the educational subsystem:"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return CHOOSE_SUBSYSTEM

def ask_for_classe(update: Update, context: CallbackContext) -> int:
    user_input, lang = update.message.text, context.user_data.get('lang', 'fr')
    subsystem_code = 'esg' if 'général' in user_input.lower() or 'general' in user_input.lower() else 'est'
    context.user_data['subsystem'] = subsystem_code
    
    classes_list = CLASSES[lang].get(subsystem_code, [])
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN
    keyboard = build_keyboard(classes_list, other_option)
    reply_text = "Veuillez choisir une classe :" if lang == 'fr' else "Please choose a class:"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSE_CLASSE

def handle_choice_or_manual(update: Update, context: CallbackContext, field_name: str, ask_next_step: callable):
    user_input, lang = update.message.text, context.user_data.get('lang', 'fr')
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN
    if user_input == other_option:
        manual_entry_prompts = {'classe': "Veuillez taper le nom de la classe :", 'module': "Veuillez taper le nom de la matière :", 'langue_contenu': "Veuillez taper la langue :"}
        manual_entry_states = {'classe': MANUAL_CLASSE, 'module': MANUAL_MATIERE, 'langue_contenu': MANUAL_LANGUE}
        reply_text = manual_entry_prompts[field_name] if lang == 'fr' else manual_entry_prompts[field_name].replace("Veuillez taper", "Please type").replace(":", "")
        update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return manual_entry_states[field_name]
    else:
        context.user_data['lesson_info'][field_name] = user_input
        return ask_next_step(update, context)

def handle_classe_choice(update: Update, context: CallbackContext) -> int:
    return handle_choice_or_manual(update, context, 'classe', ask_for_matiere)

def handle_manual_classe(update: Update, context: CallbackContext) -> int:
    context.user_data['lesson_info']['classe'] = update.message.text
    return ask_for_matiere(update, context)

def ask_for_matiere(update: Update, context: CallbackContext) -> int:
    lang, subsystem_code = context.user_data.get('lang', 'fr'), context.user_data.get('subsystem', 'esg')
    matieres_list = MATIERES[lang].get(subsystem_code, [])
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN
    keyboard = build_keyboard(matieres_list, other_option)
    reply_text = "Choisissez une matière :" if lang == 'fr' else "Choose a subject:"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSE_MATIERE

def handle_matiere_choice(update: Update, context: CallbackContext) -> int:
    return handle_choice_or_manual(update, context, 'module', ask_for_lecon)

def handle_manual_matiere(update: Update, context: CallbackContext) -> int:
    context.user_data['lesson_info']['module'] = update.message.text
    return ask_for_lecon(update, context)

def ask_for_lecon(update: Update, context: CallbackContext) -> int:
    lang = context.user_data.get('lang', 'fr')
    reply_text = "Quel est le titre exact de la leçon ?" if lang == 'fr' else "What is the exact title of the lesson?"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    return MANUAL_LECON

def ask_for_langue_contenu(update: Update, context: CallbackContext) -> int:
    context.user_data['lesson_info']['lecon'] = update.message.text
    lang = context.user_data.get('lang', 'fr')
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN
    keyboard = build_keyboard(LANGUES_CONTENU, other_option)
    reply_text = "En quelle langue le contenu doit-il être rédigé ?" if lang == 'fr' else "In which language should the content be written?"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSE_LANGUE_CONTENU

def ask_for_syllabus(update: Update, context: CallbackContext) -> int:
    return handle_choice_or_manual(update, context, 'langue_contenu', lambda u, c: (
        u.message.reply_text("Enfin, veuillez copier-coller ici l'extrait du syllabus." if c.user_data.get('lang', 'fr') == 'fr' else "Finally, please copy and paste the syllabus extract here.",
                             reply_markup=ReplyKeyboardRemove()),
        GET_SYLLABUS
    ))

def handle_manual_lang(update: Update, context: CallbackContext) -> int:
    context.user_data['lesson_info']['langue_contenu'] = update.message.text
    lang = context.user_data.get('lang', 'fr')
    update.message.reply_text("Enfin, veuillez copier-coller ici l'extrait du syllabus." if lang == 'fr' else "Finally, please copy and paste the syllabus extract here.",
                              reply_markup=ReplyKeyboardRemove())
    return GET_SYLLABUS

def generate_and_end(update: Update, context: CallbackContext) -> int:
    context.user_data['lesson_info']['syllabus'] = update.message.text
    lang_interface = context.user_data.get('lang', 'fr')
    lang_contenu_input = context.user_data['lesson_info'].get('langue_contenu', 'Français').lower()

    titles_lang_code = 'fr'
    lang_map = {'english': 'en', 'anglais': 'en', 'german': 'de', 'allemand': 'de', 'spanish': 'es', 'espagnol': 'es', 'italian': 'it', 'italien': 'it', 'chinese': 'zh', 'chinois': 'zh', 'arabic': 'ar', 'arabe': 'ar'}
    for key, value in lang_map.items():
        if key in lang_contenu_input:
            titles_lang_code = value
            break
    
    selected_titles = TITLES.get(titles_lang_code, TITLES['fr'])

    wait_message = ("✅ Merci ! Informations collectées.\n🧠 Préparation de votre fiche de leçon...") if lang_interface == 'fr' else ("✅ Thank you! Information collected.\n🧠 Preparing your lesson plan...")
    update.message.reply_text(wait_message)

    info = context.user_data['lesson_info']
    final_prompt = PROMPT_UNIVERSAL.format(
        classe=info.get('classe', 'N/A'), module=info.get('module', 'N/A'),
        lecon=info.get('lecon', 'N/A'), langue_contenu=info.get('langue_contenu', 'Français'),
        syllabus=info.get('syllabus', 'N/A'), **selected_titles
    )

    generated_text = call_openai_api(final_prompt)
    logger.info("Texte de la leçon généré.")

    update.message.reply_text("✅ Leçon générée ! Voici un aperçu.")
    preview_text = generated_text.split("<bilingual_data>")[0]
    for i in range(0, len(preview_text), 4096):
        update.message.reply_text(preview_text[i:i+4096])

    update.message.reply_text("<i>Génération du fichier PDF...</i>", parse_mode=ParseMode.HTML)
    pdf_filename = f"Fiche_Lecon_{info.get('lecon', 'lecon').replace(' ', '_')}.pdf"

    if create_pdf_with_pandoc(generated_text, pdf_filename, lang_contenu_code=titles_lang_code):
        update.message.reply_text("✅ PDF généré avec succès !")
        with open(pdf_filename, 'rb') as pdf_file:
            context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file)
        os.remove(pdf_filename)
    else:
        update.message.reply_text("❌ La création du PDF a échoué. Vérifiez les logs pour les détails.")
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Opération annulée.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
# =======================================================================
# FIN DE LA SECTION 5
# =======================================================================


# =======================================================================
# SECTION 6 : Lancement du Bot
# =======================================================================
def main():
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Serveur Flask pour le Health Check démarré.")

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_LANG: [MessageHandler(Filters.regex('^(Français 🇫🇷|English 🇬🇧)$'), select_lang)],
            SELECT_OPTION: [MessageHandler(Filters.regex('^(Préparer une leçon|Prepare a lesson)$'), ask_for_subsystem)],
            CHOOSE_SUBSYSTEM: [MessageHandler(Filters.text & ~Filters.command, ask_for_classe)],
            CHOOSE_CLASSE: [MessageHandler(Filters.text & ~Filters.command, handle_classe_choice)],
            MANUAL_CLASSE: [MessageHandler(Filters.text & ~Filters.command, handle_manual_classe)],
            CHOOSE_MATIERE: [MessageHandler(Filters.text & ~Filters.command, handle_matiere_choice)],
            MANUAL_MATIERE: [MessageHandler(Filters.text & ~Filters.command, handle_manual_matiere)],
            MANUAL_LECON: [MessageHandler(Filters.text & ~Filters.command, ask_for_langue_contenu)],
            CHOOSE_LANGUE_CONTENU: [MessageHandler(Filters.text & ~Filters.command, ask_for_syllabus)],
            MANUAL_LANGUE: [MessageHandler(Filters.text & ~Filters.command, handle_manual_lang)],
            GET_SYLLABUS: [MessageHandler(Filters.text & ~Filters.command, generate_and_end)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=10*60
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    logger.info("✅ Bot MINESEC IA démarré...")
    updater.idle()

if __name__ == '__main__':
    main()
# =======================================================================
# FIN DE LA SECTION 6
# =======================================================================