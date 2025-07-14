# =======================================================================
# CELLULE PRINCIPALE DU BOT (mettez tout le code suivant dans une deuxième cellule)
# =======================================================================

# =======================================================================
# SECTION 1 : IMPORTS (VERSION NETTOYÉE)
# =======================================================================
import os
import logging
import re
import pypandoc
import datetime
import locale
import openai
from flask import Flask
import threading
from openai import OpenAI

#from google.colab import userdata

# Imports de la librairie python-telegram-bot
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
)
# =======================================================================
# FIN DE LA SECTION 1 IMPORTS
# =======================================================================


# =======================================================================
# SECTION 2 : CONFIGURATION ET CLÉS API (VERSION NETTOYÉE)
# =======================================================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("ERREUR : Clés API manquantes. Vérifiez les 'Secrets' (🔑) de Colab.")

# On crée une seule instance du client OpenAI.
client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration du logging.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =======================================================================
# FIN DE LA SECTION 2 : CONFIGURATION ET CLÉS API
# =======================================================================
# # =======================================================================
# SECTION 2.5 : DICTIONNAIRE DE TRADUCTIONS (VERSION FINALE COMPLÈTE)
# Ce dictionnaire centralise toutes les traductions des titres pour le prompt.
# =======================================================================
TITLES = {
    'fr': {
        "FICHE_DE_LECON": "FICHE DE LEÇON APC",
        "OBJECTIFS": "OBJECTIFS PÉDAGOGIQUES",
        "SITUATION_PROBLEME": "SITUATION PROBLÈME",
        "DEROULEMENT": "DÉROULEMENT DE LA LEÇON",
        "INTRODUCTION": "Introduction (5 min)",
        "ACTIVITE_1": "Activité 1: Découverte (10 min)",
        "ACTIVITE_2": "Activité 2: Conceptualisation et TRACE ÉCRITE (20 min)",
        "TRACE_ECRITE": "Trace Écrite",
        "ACTIVITE_3": "Activité 3: Application (10 min)",
        "DEVOIRS": "DEVOIRS",
        "JEU_BILINGUE": "JEU BILINGUE / BILINGUAL GAME",
        "HEADER_MATIERE": "Matière",
        "HEADER_CLASSE": "Classe",
        "HEADER_DUREE": "Durée",
        "HEADER_LECON": "Leçon du jour",
        "PDF_TITLE": "Fiche de Leçon",
        "PDF_AUTHOR": "Assistant Pédagogique MINESEC IA"
    },
    'en': {
        "FICHE_DE_LECON": "CBA LESSON PLAN",
        "OBJECTIFS": "LEARNING OBJECTIVES",
        "SITUATION_PROBLEME": "PROBLEM SITUATION",
        "DEROULEMENT": "LESSON PLAN",
        "INTRODUCTION": "Introduction (5 min)",
        "ACTIVITE_1": "Activity 1: Discovery (10 min)",
        "ACTIVITE_2": "Activity 2: Conceptualization and WRITTEN RECORD (20 min)",
        "TRACE_ECRITE": "Written Record",
        "ACTIVITE_3": "Activity 3: Application (10 min)",
        "DEVOIRS": "HOMEWORK",
        "JEU_BILINGUE": "BILINGUAL GAME / JEU BILINGUE",
        "HEADER_MATIERE": "Subject",
        "HEADER_CLASSE": "Class",
        "HEADER_DUREE": "Duration",
        "HEADER_LECON": "Lesson of the Day",
        "PDF_TITLE": "Lesson Plan",
        "PDF_AUTHOR": "MINESEC IA Pedagogical Assistant"
    },
    'de': {
        "FICHE_DE_LECON": "LEKTIONSPLAN (CBA)",
        "OBJECTIFS": "LERNZIELE",
        "SITUATION_PROBLEME": "PROBLEMSITUATION",
        "DEROULEMENT": "LEKTIONSVERLAUF",
        "INTRODUCTION": "Einführung (5 min)",
        "ACTIVITE_1": "Aktivität 1: Entdeckung (10 min)",
        "ACTIVITE_2": "Aktivität 2: Konzeptualisierung und SCHRIFTLICHER EINTRAG (20 min)",
        "TRACE_ECRITE": "Schriftlicher Eintrag",
        "ACTIVITE_3": "Aktivität 3: Anwendung (10 min)",
        "DEVOIRS": "HAUSAUFGABEN",
        "JEU_BILINGUE": "ZWEISPRACHIGES SPIEL / BILINGUAL GAME",
        "HEADER_MATIERE": "Fach",
        "HEADER_CLASSE": "Klasse",
        "HEADER_DUREE": "Dauer",
        "HEADER_LECON": "Heutige Lektion",
        "PDF_TITLE": "Lektionsplan",
        "PDF_AUTHOR": "Pädagogischer Assistent MINESEC IA"
    },
    'es': {
        "FICHE_DE_LECON": "FICHA DE LECCIÓN (APC)",
        "OBJECTIFS": "OBJETIVOS DE APRENDIZAJE",
        "SITUATION_PROBLEME": "SITUACIÓN PROBLEMA",
        "DEROULEMENT": "DESARROLLO DE LA LECCIÓN",
        "INTRODUCTION": "Introducción (5 min)",
        "ACTIVITE_1": "Actividad 1: Descubrimiento (10 min)",
        "ACTIVITE_2": "Actividad 2: Conceptualización y REGISTRO ESCRITO (20 min)",
        "TRACE_ECRITE": "Registro Escrito",
        "ACTIVITE_3": "Actividad 3: Aplicación (10 min)",
        "DEVOIRS": "TAREAS",
        "JEU_BILINGUE": "JUEGO BILINGÜE / BILINGUAL GAME",
        "HEADER_MATIERE": "Asignatura",
        "HEADER_CLASSE": "Clase",
        "HEADER_DUREE": "Duración",
        "HEADER_LECON": "Lección del Día",
        "PDF_TITLE": "Ficha de Lección",
        "PDF_AUTHOR": "Asistente Pedagógico MINESEC IA"
    },
    'zh': {
        "FICHE_DE_LECON": "CBA 课程计划",
        "OBJECTIFS": "学习目标",
        "SITUATION_PROBLEME": "问题情境",
        "DEROULEMENT": "课程计划",
        "INTRODUCTION": "介绍 (5 分钟)",
        "ACTIVITE_1": "活动1：发现 (10 分钟)",
        "ACTIVITE_2": "活动2：概念化和书面记录 (20 分钟)",
        "TRACE_ECRITE": "书面记录",
        "ACTIVITE_3": "活动3：应用 (10 分钟)",
        "DEVOIRS": "家庭作业",
        "JEU_BILINGUE": "双语游戏 / BILINGUAL GAME",
        "HEADER_MATIERE": "科目",
        "HEADER_CLASSE": "班级",
        "HEADER_DUREE": "时长",
        "HEADER_LECON": "今日课程"
    },
    'ar': {
        "FICHE_DE_LECON": "خطة درس (المنهج القائم على الكفايات)",
        "OBJECTIFS": "الأهداف التعليمية",
        "SITUATION_PROBLEME": "الوضعية المشكلة",
        "DEROULEMENT": "خطة الدرس",
        "INTRODUCTION": "مقدمة (5 دقائق)",
        "ACTIVITE_1": "نشاط 1: اكتشاف (10 دقائق)",
        "ACTIVITE_2": "نشاط 2: وضع المفاهيم والسجل المكتوب (20 دقيقة)",
        "TRACE_ECRITE": "السجل المكتوب",
        "ACTIVITE_3": "نشاط 3: تطبيق (10 دقائق)",
        "DEVOIRS": "واجب منزلي",
        "JEU_BILINGUE": "لعبة ثنائية اللغة / BILINGUAL GAME",
        "HEADER_MATIERE": "المادة",
        "HEADER_CLASSE": "الفصل",
        "HEADER_DUREE": "المدة",
        "HEADER_LECON": "درس اليوم",
        "PDF_TITLE": "خطة الدرس",
        "PDF_AUTHOR": "مساعد التدريس MINESEC IA"
    },
    'it': { # Italien
        "FICHE_DE_LECON": "PIANO DI LEZIONE (APC)",
        "OBJECTIFS": "OBIETTIVI DI APPRENDIMENTO",
        "SITUATION_PROBLEME": "SITUAZIONE PROBLEMATICA",
        "DEROULEMENT": "SVOLGIMENTO DELLA LEZIONE",
        "INTRODUCTION": "Introduzione (5 min)",
        "ACTIVITE_1": "Attività 1: Scoperta (10 min)",
        "ACTIVITE_2": "Attività 2: Concettualizzazione e TRACCIA SCRITTA (20 min)",
        "TRACE_ECRITE": "Traccia Scritta",
        "ACTIVITE_3": "Attività 3: Applicazione (10 min)",
        "DEVOIRS": "COMPITI PER CASA",
        "JEU_BILINGUE": "GIOCO BILINGUE / BILINGUAL GAME",
        "HEADER_MATIERE": "Materia",
        "HEADER_CLASSE": "Classe",
        "HEADER_DUREE": "Durata",
        "HEADER_LECON": "Lezione del Giorno",
        "PDF_TITLE": "Piano di Lezione",
        "PDF_AUTHOR": "Assistente Pedagogico MINESEC IA",
        "PDF_TITLE": "课程计划",
        "PDF_AUTHOR": "MINESEC IA 教学助理"
    }
}
# =======================================================================
# FIN DE LA SECTION 2.5
# =======================================================================
# =======================================================================
# SECTION 2.6 : LISTES D'OPTIONS POUR LES MENUS
# (Ce bloc est NOUVEAU et doit être ajouté à votre code)
# =======================================================================
AUTRE_OPTION_FR = "✍️ Autre (préciser)"
AUTRE_OPTION_EN = "✍️ Other (specify)"

# --- SOUS-SYSTÈMES ---
SUBSYSTEME_FR = ['Enseignement Secondaire Général (ESG)', 'Enseignement Secondaire Technique (EST)']
SUBSYSTEME_EN = ['General Education', 'Technical Education']

# --- CLASSES (Structurées par langue et sous-système) ---
CLASSES = {
    'fr': {
        'esg': ['6ème', '5ème', '4ème', '3ème', 'Seconde', 'Première', 'Terminale'],
        'est': ['1ère Année CAP', '2ème Année CAP', 'Seconde Technique', 'Première Technique', 'Terminale Technique']
    },
    'en': {
        'esg': ['Form 1', 'Form 2', 'Form 3', 'Form 4', 'Form 5', 'Lower Sixth', 'Upper Sixth'],
        'est': ['Year 1 (Technical)', 'Year 2 (Technical)', 'Form 4 (Technical)', 'Form 5 (Technical)', 'Upper Sixth (Technical)']
    }
}

# --- MATIÈRES (Structurées par langue et sous-système) ---
MATIERES = {
    'fr': {
        'esg': ['Mathématiques', 'Physique', 'Chimie', 'SVT', 'Français', 'Histoire', 'Géographie', 'Philosophie', 'Anglais', 'ECM', 'Espagnol', 'Italien', 'Chinois', 'Allemand' ],
        'est': ['Dessin Technique', 'Mécanique', 'Électrotechnique', 'Comptabilité']
    },
    'en': {
        'esg': ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'History', 'Geography', 'Economics', 'Further Maths', 'Computer Science', 'English', 'French', 'ICT', 'Additional Maths', 'Logic', 'Geology'],
        'est': ['Technical Drawing', 'Mechanics', 'Electrotechnics', 'Accounting']
    }
}

# --- LANGUES DU CONTENU ---
LANGUES_CONTENU = ['Français', 'English', 'Deutsch', 'Español', 'Italiano', '中文 (Chinois)', 'العربية (Arabe)']
# =======================================================================
# FIN DE LA SECTION 2.6
# =======================================================================

# =======================================================================
# SECTION 3 : LE "PROMPT MAÎTRE" (VERSION "CONTRÔLE QUALITÉ")
# =======================================================================
PROMPT_UNIVERSAL = """Tu es MINESEC IA, un expert en ingénierie pédagogique pour le Cameroun.

**RÈGLES ABSOLUES DE FORMATAGE :**
1.  **Format Principal :** Tu DOIS utiliser le formatage **Markdown**.
2.  **Gras :** Utilise `**Texte en gras**` pour TOUS les titres et sous-titres.
3.  **Italique :** Utilise `*Texte en italique*` pour les instructions ou les exemples.
4.  **Listes :** Utilise TOUJOURS un tiret `-` pour les listes à puces.
5.  **Formules :** Utilise le format LaTeX (`$...$` ou `$$...$$`).
6.  **INTERDICTION FORMELLE :** N'utilise JAMAIS, sous aucun prétexte, de balises HTML (`<b>`, `<i>`) ni de blocs de code Markdown (comme ` ```markdown ... ``` `). Ta réponse doit commencer DIRECTEMENT par le premier titre, sans aucune introduction ou balise d'enveloppement.
6.  **INTERDICTION FORMELLE :** N'utilise JAMAIS de balises HTML...
7.  **IMPORTANT :** Les titres de section (comme `**{objectifs}**`) ne doivent JAMAIS commencer par une puce de liste (`-`, `*`, ou `•`). Ils doivent être sur leur propre ligne.

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
*(Rédige ici un scénario détaillé et contextualisé au Cameroun avec Contexte, Tâche, et Consignes.Voici un exemple: Voici un texte synthétique en trois paragraphes, directement exploitable comme situation-problème contextualisée pour une leçon APC en TIC au Cameroun :

Ton oncle vient de rénover sa maison à Garoua et a installé plusieurs appareils modernes : caméra de surveillance, ampoules connectées et une serrure automatique. Il t’a vu contrôler tous ces objets depuis ton téléphone et a été très surpris. Il te demande alors comment tout cela fonctionne.

Tu te rends compte qu’il ne connaît pas le concept d’objets connectés, ni la façon dont ils communiquent entre eux ou avec le téléphone. Tu décides donc de lui expliquer, avec des mots simples, ce qu’est l’Internet des Objets (IoT) et comment ces appareils peuvent fonctionner ensemble grâce à une connexion réseau.

Pour l’aider à mieux comprendre, tu vas lui préparer une courte présentation ou une fiche illustrée qui décrit le fonctionnement de l’IoT à la maison, en prenant des exemples concrets comme l’ampoule intelligente, la caméra Wi-Fi ou la serrure connectée.)*

**{deroulement}**

**{introduction}:**
*- Rédige une ou plusieurs questions de rappel des pré-requis necessaires a la comprehension de la nouvelle lecon.*

**{activite_1}:**
*- Rédige le contenu d'une activité de découverte.*
<!--
INSTRUCTIONS POUR CETTE SECTION:
tu dois concevoir une activite qui va permettre aux eleves de decouvrir les concepts cles lies aux ojectifs de la lecon.
-->

**{activite_2}:**
- **{trace_ecrite}:** *(Rédige ici le cours complet et détaillé (minimum 400 mots) dans le style d'un cours MINESEC.)*
<!--
INSTRUCTIONS POUR CETTE SECTION:
tu dois proposer un cours qui explique le plus simplement et detaille possibles les differents concepts de la lecon donnes dans les objectifs.
tu devras utiliser des formules proprietes, tableaux ou lillustrations quand necessaire.
pour les cours scientifiques il faut mettre un accent sur le trace des courbes, tableau de variation, formule chimiques etc...
-->

**{activite_3}:**
*- Rédige un exercice d'application complet à faire en classe, suivi de son corrigé détaillé.*
<!--
INSTRUCTIONS POUR CETTE SECTION:
tu dois concevoir un exercice qui traite des principaux ojectifs de la lecon et leur corrige detaille.
-->

**{devoirs}**
*(Rédige 2 exercices complets pour la maison.)*

<bilingual_data>
<!--
INSTRUCTIONS POUR CETTE SECTION:
Génère ici 5 lignes de données pour le tableau bilingue, en suivant ces règles STRICTES:
1. Chaque ligne doit contenir un MOT CLÉ pertinent tiré de la leçon.
2. N'utilise PAS de mots génériques comme "Mot1", "Word1". Utilise de VRAIS mots.
3. Sépare les colonnes avec un point-virgule ';'.

RÈGLES DE TRADUCTION :
- Si la langue de la leçon est 'Français' -> Format: MotEnFrançais;TraductionEnAnglais
- Si la langue de la leçon est 'Anglais' -> Format: MotEnAnglais;TraductionEnFrançais
- Si la langue de la leçon est une autre (Allemand, Espagnol, etc.) -> Format: MotDansLaLangue;TraductionEnFrançais;TraductionEnAnglais

Commence à générer les 5 lignes de données MAINTENANT.
-->
</bilingual_data>
"""
# =======================================================================
# FIN DE LA SECTION 3
# =======================================================================



# =======================================================================
# SECTION 4 : FONCTIONS UTILITAIRES (VERSION STABLE ET CORRIGÉE)
# =======================================================================

def build_keyboard(items, other_option_label, items_per_row=2):
    """Construit un clavier de boutons à partir d'une liste d'items."""
    keyboard = [items[i:i + items_per_row] for i in range(0, len(items), items_per_row)]
    if other_option_label:
        keyboard.append([other_option_label])
    return keyboard

def call_openai_api(prompt):
    """Appelle l'API OpenAI. Cette fonction est correcte."""
    try:
        logger.info("Appel à l'API OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API OpenAI: {e}")
        return f"Désolé, une erreur est survenue. Détails: {e}"


# Voici la SEULE et UNIQUE version de la fonction de création de PDF.
# Elle est placée correctement dans la section des fonctions utilitaires.

def create_pdf_with_pandoc(text, filename="document.pdf", lang_contenu_code='fr'):
    """
    Crée un PDF de haute qualité en utilisant Pandoc.
    Elle génère le texte principal ET un tableau Markdown pour le jeu bilingue.
    """
    try:
        logger.info(f"Création du PDF (v6 - Tableau Markdown) : {filename}")

        # 1. On sépare le texte principal et les données du jeu bilingue
        if "<bilingual_data>" in text:
            main_markdown_raw = text.split("<bilingual_data>")[0]
            bilingual_data = text.split("<bilingual_data>")[1].split("</bilingual_data>")[0]
        else:
            main_markdown_raw = text
            bilingual_data = ""

        # 2. On nettoie les commentaires et on standardise le texte principal
        # Cette étape est importante pour la consistance.
        main_markdown_final = re.sub(r'<!--.*?-->', '', main_markdown_raw, flags=re.DOTALL).strip()
        
        # 3. On construit le tableau bilingue en format Markdown s'il existe
        markdown_table = "" # On initialise une chaîne vide pour le tableau
        if bilingual_data:
            # On nettoie le contenu du tableau
            bilingual_content = re.sub(r'<!--.*?-->', '', bilingual_data, flags=re.DOTALL).strip()
            lines = [line.strip() for line in bilingual_content.split('\n') if line.strip() and ';' in line]
            
            if lines:
                # On récupère le titre du tableau dans la bonne langue (langue du contenu)
                table_title = TITLES.get(lang_contenu_code, TITLES['fr'])['JEU_BILINGUE']
                
                # On crée la section complète du tableau en Markdown
                markdown_table += f"\n\n**{table_title}**\n\n"
                
                # On définit les en-têtes en fonction de la langue du contenu
                headers = ['N°', 'Français', 'English'] if lang_contenu_code == 'fr' else ['N°', 'English', 'Français']
                
                # Construction du tableau Markdown
                markdown_table += f"| {headers[0]} | {headers[1]} | {headers[2]} |\n"
                markdown_table += "|:---:|:---|:---|\n" # Ligne pour l'alignement des colonnes
                
                for i, line in enumerate(lines):
                    parts = [p.strip() for p in line.split(';')]
                    if len(parts) == 2:
                        markdown_table += f"| {i+1} | {parts[0]} | {parts[1]} |\n"

        # 4. On assemble le document Markdown final : texte principal + tableau
        final_markdown_doc = main_markdown_final + markdown_table

        # 5. On crée l'en-tête YAML pour Pandoc pour un rendu professionnel
        selected_pdf_titles = TITLES.get(lang_contenu_code, TITLES['fr'])
        
        # Configuration de la locale pour la date
        try:
            # Pour le chinois, la locale peut être complexe. On utilise 'en_US' comme fallback sûr.
            locale_str = f'{lang_contenu_code}_{lang_contenu_code.upper()}.UTF-8' if lang_contenu_code != 'zh' else 'en_US.UTF-8'
            locale.setlocale(locale.LC_TIME, locale_str)
        except locale.Error:
            locale.setlocale(locale.LC_TIME, '') # Fallback à la locale système

        formatted_date = datetime.date.today().strftime('%d %B %Y')


        yaml_header = f"""
---
title: "{selected_pdf_titles.get('PDF_TITLE', 'Lesson Plan')}"
author: "{selected_pdf_titles.get('PDF_AUTHOR', 'MINESEC IA')}"
date: "{formatted_date}"
documentclass: article
fontsize: 11pt
geometry: "margin=1in"
---
"""
        # 6. On assemble le tout et on convertit avec le moteur XeLaTeX
        document_source = yaml_header + final_markdown_doc
        pypandoc.convert_text(document_source, 'pdf', format='markdown',
                              outputfile=filename,
                              extra_args=['--pdf-engine=xelatex']) # XeLaTeX est excellent pour les langues
        
        logger.info(f"PDF '{filename}' créé avec succès en utilisant Pandoc et XeLaTeX.")
        return True

    except Exception as e:
        logger.error(f"Erreur DÉFINITIVE lors de la création du PDF avec Pandoc: {e}")
        # Log supplémentaire pour le débogage si une erreur se produit
        if 'document_source' in locals():
            logger.error(f"Source Markdown problématique (extrait) : {document_source[:1000]}")
        return False
    
# --- Fonction pour le mini-serveur web (Health Check pour Render) ---
def run_flask_app():
    app = Flask(__name__)
    @app.route('/health')
    def health_check():
        return "OK", 200 # Répond "OK" à Render
    
   
# =======================================================================
# FIN DE LA SECTION 4 : FONCTIONS UTILITAIRES
# =======================================================================


# =======================================================================
# SECTION 5 : LOGIQUE DE CONVERSATION (VERSION MENUS GUIDÉS - ROBUSTE)
# =======================================================================

# --- Nouveaux états pour la conversation avec menus ---
(SELECT_LANG, SELECT_OPTION, CHOOSE_SUBSYSTEM,
 CHOOSE_CLASSE, MANUAL_CLASSE,
 CHOOSE_MATIERE, MANUAL_MATIERE,
 MANUAL_LECON,
 CHOOSE_LANGUE_CONTENU, MANUAL_LANGUE,
 GET_SYLLABUS) = range(11)


# --- Fonctions de démarrage ---
def start(update: Update, context: CallbackContext) -> int:
    keyboard = [['Français 🇫🇷'], ['English 🇬🇧']]
    update.message.reply_text(
        "Bonjour! Je suis MINESEC IA. Choisissez votre langue.\n\n"
        "Hello! I am MINESEC IA. Please choose your language.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECT_LANG

def select_lang(update: Update, context: CallbackContext) -> int:
    lang_choice = update.message.text
    if 'Français' in lang_choice:
        context.user_data['lang'] = 'fr'
        options = [['Préparer une leçon'], ['Produire une évaluation (bientôt)']]
        reply_text = "Langue sélectionnée : Français. Que souhaitez-vous faire ?"
    elif 'English' in lang_choice:
        context.user_data['lang'] = 'en'
        options = [['Prepare a lesson'], ['Create an assessment (soon)']]
        reply_text = "Language selected: English. What would you like to do?"
    else:
        update.message.reply_text("Choix invalide. /start pour recommencer.")
        return ConversationHandler.END
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(options, one_time_keyboard=True))
    return SELECT_OPTION


# --- Nouveau flux guidé par menus ---

def ask_for_subsystem(update: Update, context: CallbackContext) -> int:
    """Demande le sous-système d'enseignement (ESG/EST)."""
    context.user_data['lesson_info'] = {}
    lang = context.user_data.get('lang', 'fr')
    subsystem_list = SUBSYSTEME_FR if lang == 'fr' else SUBSYSTEME_EN
    keyboard = [[s] for s in subsystem_list]
    reply_text = "Veuillez sélectionner le sous-système d'enseignement :" if lang == 'fr' else "Please select the educational subsystem:"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return CHOOSE_SUBSYSTEM

def ask_for_classe(update: Update, context: CallbackContext) -> int:
    """Affiche le menu de sélection de la classe."""
    user_input = update.message.text
    lang = context.user_data.get('lang', 'fr')
    subsystem_code = 'esg' if 'général' in user_input.lower() or 'general' in user_input.lower() else 'est'
    context.user_data['subsystem'] = subsystem_code

    if subsystem_code == 'est':
        reply_text = "Le sous-système Technique est en cours de développement. Veuillez redémarrer avec /start et choisir ESG."
        update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    classes_list = CLASSES[lang][subsystem_code]
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN
    keyboard = build_keyboard(classes_list, other_option)
    reply_text = "Veuillez choisir une classe :" if lang == 'fr' else "Please choose a class:"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSE_CLASSE

def handle_classe_choice(update: Update, context: CallbackContext) -> int:
    """Gère le choix de la classe et demande la matière."""
    user_input = update.message.text
    lang = context.user_data.get('lang', 'fr')
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN

    if user_input == other_option:
        reply_text = "Veuillez taper le nom de la classe :" if lang == 'fr' else "Please type the class name:"
        update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return MANUAL_CLASSE
    else:
        context.user_data['lesson_info']['classe'] = user_input
        return ask_for_matiere(update, context)

def handle_manual_classe(update: Update, context: CallbackContext) -> int:
    """Stocke la classe manuelle et demande la matière."""
    context.user_data['lesson_info']['classe'] = update.message.text
    return ask_for_matiere(update, context)

def ask_for_matiere(update: Update, context: CallbackContext) -> int:
    """Affiche le menu de sélection de la matière."""
    lang = context.user_data.get('lang', 'fr')
    subsystem_code = context.user_data.get('subsystem', 'esg')
    matieres_list = MATIERES[lang][subsystem_code]
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN
    keyboard = build_keyboard(matieres_list, other_option)
    reply_text = "Choisissez une matière :" if lang == 'fr' else "Choose a subject:"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSE_MATIERE

def handle_matiere_choice(update: Update, context: CallbackContext) -> int:
    """Gère le choix de la matière."""
    user_input = update.message.text
    lang = context.user_data.get('lang', 'fr')
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN

    if user_input == other_option:
        reply_text = "Veuillez taper le nom de la matière :" if lang == 'fr' else "Please type the subject name:"
        update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return MANUAL_MATIERE
    else:
        context.user_data['lesson_info']['module'] = user_input
        return ask_for_lecon(update, context)

def handle_manual_matiere(update: Update, context: CallbackContext) -> int:
    """Stocke la matière manuelle et demande la leçon."""
    context.user_data['lesson_info']['module'] = update.message.text
    return ask_for_lecon(update, context)

def ask_for_lecon(update: Update, context: CallbackContext) -> int:
    """Demande à l'utilisateur de taper le titre de la leçon."""
    lang = context.user_data.get('lang', 'fr')
    # Pour l'instant, la liste des leçons est manuelle. Le RAG viendra ici.
    reply_text = "Quel est le titre exact de la leçon ?" if lang == 'fr' else "What is the exact title of the lesson?"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    return MANUAL_LECON

def ask_for_langue_contenu(update: Update, context: CallbackContext) -> int:
    """Demande la langue de rédaction du contenu."""
    context.user_data['lesson_info']['lecon'] = update.message.text
    lang = context.user_data.get('lang', 'fr')
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN
    keyboard = build_keyboard(LANGUES_CONTENU, other_option)
    reply_text = "En quelle langue le contenu de cette leçon doit-il être rédigé ?" if lang == 'fr' else "In which language should the content of this lesson be written?"
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSE_LANGUE_CONTENU

def ask_for_syllabus(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    lang = context.user_data.get('lang', 'fr')
    other_option = AUTRE_OPTION_FR if lang == 'fr' else AUTRE_OPTION_EN

    if user_input == other_option:
        reply_text = "Veuillez taper la langue :" if lang == 'fr' else "Please type the language:"
        update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return MANUAL_LANGUE
    else:
        context.user_data['lesson_info']['langue_contenu'] = user_input
        # *** TRADUCTION CORRIGÉE ICI ***
        reply_text = "Enfin, veuillez copier-coller ici l'extrait du syllabus." if lang == 'fr' else "Finally, please copy and paste the syllabus extract here."
        update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return GET_SYLLABUS

def handle_manual_lang(update: Update, context: CallbackContext) -> int:
    context.user_data['lesson_info']['langue_contenu'] = update.message.text
    lang = context.user_data.get('lang', 'fr')
    # *** TRADUCTION CORRIGÉE ICI ***
    reply_text = "Enfin, veuillez copier-coller ici l'extrait du syllabus." if lang == 'fr' else "Finally, please copy and paste the syllabus extract here."
    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    return GET_SYLLABUS


# --- FONCTION 8 : LA GRANDE FINALE - GÉNÉRATION ET ENVOI (VERSION FINALE CORRIGÉE) ---
# La fonction `generate_lesson` reste la même, mais nous la renommons pour plus de clarté
# --- FONCTION 8 : LA GRANDE FINALE - GÉNÉRATION ET ENVOI (VERSION CORRIGÉE ET FONCTIONNELLE) ---
def generate_and_end(update: Update, context: CallbackContext) -> int:
    # 1. On stocke la dernière information (le syllabus)
    context.user_data['lesson_info']['syllabus'] = update.message.text
    lang_interface = context.user_data.get('lang', 'fr')
    lang_contenu_input = context.user_data['lesson_info'].get('langue_contenu', 'Français').lower()

    # 2. Logique de détection de langue (ne change pas)
    titles_lang_code = 'fr'
    if any(lang in lang_contenu_input for lang in ['english', 'anglais']): titles_lang_code = 'en'
    elif any(lang in lang_contenu_input for lang in ['german', 'allemand']): titles_lang_code = 'de'
    elif any(lang in lang_contenu_input for lang in ['spanish', 'espagnol']): titles_lang_code = 'es'
    elif any(lang in lang_contenu_input for lang in ['italian', 'italien']): titles_lang_code = 'it'
    elif any(lang in lang_contenu_input for lang in ['chinese', 'chinois']): titles_lang_code = 'zh'
    elif any(lang in lang_contenu_input for lang in ['arabic', 'arabe']): titles_lang_code = 'ar'
    selected_titles = TITLES.get(titles_lang_code, TITLES['fr'])

    # 3. Message d'attente
    # *** TRADUCTION CORRIGÉE ICI ***
    wait_message = ("✅ Merci ! Toutes les informations sont collectées.\n\n"
                    "🧠 <b>Je prépare votre fiche de leçon...</b>\n\n"
                    "Ceci peut prendre une à deux minutes.") if lang_interface == 'fr' else ("✅ Thank you! All information collected.\n\n"
                    "🧠 <b>Preparing your lesson plan...</b>\n\n"
                    "This may take one to two minutes.")
    update.message.reply_text(wait_message, parse_mode=ParseMode.HTML)

    
    # 4. Préparation du prompt complet
    info = context.user_data['lesson_info']
    # On remplit le prompt avec les infos ET TOUS les titres traduits, manuellement pour éviter les erreurs.
    final_prompt = PROMPT_UNIVERSAL.format(
        # Données de la leçon
        classe=info.get('classe', 'N/A'),
        module=info.get('module', 'N/A'),
        lecon=info.get('lecon', 'N/A'),
        langue_contenu=info.get('langue_contenu', 'Français'),
        syllabus=info.get('syllabus', 'N/A'),

        # Titres de Section
        fiche_de_lecon=selected_titles["FICHE_DE_LECON"],
        objectifs=selected_titles["OBJECTIFS"],
        situation_probleme=selected_titles["SITUATION_PROBLEME"],
        deroulement=selected_titles["DEROULEMENT"],
        introduction=selected_titles["INTRODUCTION"],
        activite_1=selected_titles["ACTIVITE_1"],
        activite_2=selected_titles["ACTIVITE_2"],
        trace_ecrite=selected_titles["TRACE_ECRITE"],
        activite_3=selected_titles["ACTIVITE_3"],
        devoirs=selected_titles["DEVOIRS"],
        jeu_bilingue=selected_titles["JEU_BILINGUE"],

        # Titres de l'en-tête (CEUX QUI MANQUAIENT AVANT)
        header_matiere=selected_titles["HEADER_MATIERE"],
        header_classe=selected_titles["HEADER_CLASSE"],
        header_duree=selected_titles["HEADER_DUREE"],
        header_lecon=selected_titles["HEADER_LECON"]
    )

    # 5. Appel à l'IA
    generated_text = call_openai_api(final_prompt)
    logger.info("Texte de la leçon généré par l'IA.")

    # 6. Envoi d'un aperçu dans le chat
    apercu_message = "✅ Leçon générée ! Voici un aperçu. Le rendu final des formules sera dans le PDF."
    update.message.reply_text(apercu_message)
    # On envoie un extrait du texte généré (sans le tableau)
    preview_text = generated_text.split("<bilingual_data>")[0]
    for i in range(0, len(preview_text), 4096):
        update.message.reply_text(preview_text[i:i+4096])

    # 7. APPEL CORRECT À LA FONCTION DE CRÉATION DE PDF
    pdf_message = "<i>Génération du fichier PDF en cours...</i>"
    update.message.reply_text(pdf_message, parse_mode=ParseMode.HTML)
    pdf_filename = f"Fiche_Lecon_{info.get('lecon', 'lecon').replace(' ', '_')}.pdf"

    # On appelle notre fonction propre de la Section 4
    if create_pdf_with_pandoc(generated_text, pdf_filename, lang_contenu_code=titles_lang_code):
        # Le PDF a réussi ! On l'envoie.
        success_message = "✅ PDF généré avec succès !"
        update.message.reply_text(success_message)
        with open(pdf_filename, 'rb') as pdf_file:
            context.bot.send_document(chat_id=update.effective_chat.id, document=pdf_file)
        os.remove(pdf_filename)
    else:
        # Le PDF a échoué. On envoie un message d'excuse.
        error_message = "❌ La création du fichier PDF a échoué. Veuillez vérifier les logs de Colab pour les détails de l'erreur."
        update.message.reply_text(error_message)

    # 8. On termine la conversation.
    return ConversationHandler.END



def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Opération annulée.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# =======================================================================
# SECTION 6 : Lancement du Bot (CONFIGURATION FINALE DES ÉTATS)
# =======================================================================
def main():
    # --- Configuration et lancement du bot Telegram (votre code existant) ---
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
        conversation_timeout=5*60 # Timeout de 5 minutes
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    logger.info("✅ Bot MINESEC IA (v5 - Menus Stables) démarré...")
    updater.idle()

if __name__ == '__main__':
    
    main()

# =======================================================================
# FIN DE LA SECTION 6 : Lancement du Bot
# =======================================================================