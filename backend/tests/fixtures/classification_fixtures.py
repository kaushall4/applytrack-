# (text, expected_intent, language)
FIXTURES = [
    # REJECTION DE — Compliment-Sandwich
    ("Wir haben Ihre Unterlagen sorgfaeltig geprueft und moechten betonen, dass uns Ihr "
     "Profil und Ihre Qualifikationen sehr beeindruckt haben. Dennoch haben wir Bewerbungen "
     "erhalten, die die spezifischen Anforderungen der Position umfassender erfuellen. Daher "
     "muessen wir Ihnen leider mitteilen, dass Ihre Bewerbung diesmal nicht erfolgreich war.",
     "rejection", "de"),
    ("Vielen Dank fuer Ihr Interesse und die Zeit, die Sie in Ihre Bewerbung investiert "
     "haben. Nach reiflicher Ueberlegung haben wir uns jedoch fuer eine andere Kandidatin "
     "entschieden. Wir wuenschen Ihnen alles Gute.",
     "rejection", "de"),
    ("Es freut uns, dass Sie sich beworben haben. Leider koennen wir Ihre Bewerbung zum "
     "jetzigen Zeitpunkt nicht weiter beruecksichtigen.",
     "rejection", "de"),
    ("Die Stelle wurde inzwischen anderweitig vergeben. Wir danken Ihnen fuer Ihr "
     "Verstaendnis.",
     "rejection", "de"),
    # REJECTION EN
    ("Thank you so much for applying and for sharing your impressive background. After "
     "careful consideration, we have decided to move forward with other candidates whose "
     "experience more closely matches the role.",
     "rejection", "en"),
    ("We enjoyed reviewing your profile and were impressed by your achievements. "
     "Unfortunately, we will not be proceeding with your application for this position.",
     "rejection", "en"),
    # APPLICATION_RECEIVED DE
    ("Vielen Dank fuer Ihre Bewerbung als Praktikant im Wealth Management. Wir haben Ihre "
     "Unterlagen erhalten und werden diese sorgfaeltig pruefen. Wir melden uns in Kuerze.",
     "application_received", "de"),
    ("Besten Dank fuer Ihr Interesse. Den Eingang Ihrer Bewerbung koennen wir hiermit "
     "bestaetigen. Ihre Bewerbung befindet sich in Bearbeitung.",
     "application_received", "de"),
    # APPLICATION_RECEIVED EN
    ("Thank you for your application. We have received your documents and your application "
     "is currently being reviewed. We will be in touch.",
     "application_received", "en"),
    # INTERVIEW_INVITE DE
    ("Wir freuen uns, Sie naeher kennenzulernen, und moechten Sie zu einem "
     "Vorstellungsgespraech einladen. Bitte teilen Sie uns Ihre Verfuegbarkeit mit.",
     "interview_invite", "de"),
    ("Ihre Bewerbung hat uns ueberzeugt. Als naechster Schritt moechten wir ein "
     "telefonisches Interview fuehren.",
     "interview_invite", "de"),
    # INTERVIEW_INVITE EN
    ("We were impressed by your application and would like to invite you to a first "
     "interview. Could you let us know your availability?",
     "interview_invite", "en"),
    # NEXT_ROUND DE
    ("Vielen Dank fuer das angenehme Erstgespraech. Wir wuerden Sie gerne zu einer zweiten "
     "Runde einladen, in der Sie eine kurze Fallstudie bearbeiten.",
     "next_round", "de"),
    # OFFER DE
    ("Wir freuen uns sehr, Ihnen die Stelle anbieten zu duerfen. Im Anhang finden Sie den "
     "Arbeitsvertrag zur Durchsicht.",
     "offer", "de"),
    # INFO_REQUEST DE
    ("Vielen Dank fuer Ihre Bewerbung. Fuer die weitere Bearbeitung benoetigen wir noch Ihr "
     "Arbeitszeugnis sowie einen aktuellen Notenauszug. Koennten Sie uns diese nachreichen?",
     "info_request", "de"),
    # NOT_APPLICATION_RELATED EN
    ("New jobs matching your profile: 12 new roles in Banking & Finance near Zurich. View "
     "and apply on LinkedIn.",
     "not_application_related", "en"),
]
