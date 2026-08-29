"""
Avatar quick-reply phrases -- pre-recorded signed replies a hearing person
can trigger for the Deaf patient, as an alternative to the existing
speech-to-text "Listen to Reply" path.

Every clip here MUST be real footage of an actual signer, never AI-generated.
A general-purpose photo/video-avatar tool (CapCut, Hedra, and similar) has no
grounding in real sign-language data -- it will produce a hand-shaped motion
that looks plausible and means nothing in actual ISL. Every production sign-
avatar system that claims real accuracy (Sign-Speak/NTID, SignAvatar
research, etc.) grounds its output in real signer motion-capture or a vetted
sign dictionary; a general avatar generator has neither. See PHASE_AVATAR.md
for the reasoning in full.

`video` is None for a phrase with no recorded clip yet -- the UI shows those
as "coming soon", never as a fake or silently-broken button. Fill in `video`/
`poster` here the moment real footage exists; nothing else needs to change.
"""

AVATAR_REPLIES = [
    {
        "key": "hello",
        "label": "Hello",
        "video": "hello.mp4",
        "poster": "hello_poster.jpg",
        "icon": "fa-hand-sparkles",
        "triggers": [
            # English
            "hello", "hi", "hey", "good morning", "good evening", "greetings",
            # Hindi
            "namaste", "namaskar", "pranam",
            "नमस्ते", "नमस्कार", "प्रणाम", "हेलो",
            # Bengali
            "nomoshkar", "nomoskar", "pronam", "shuvo shokal",
            "নমস্কার", "হ্যালো", "প্রণাম", "শুভ সকাল"
        ],
    },
    {
        "key": "yes",
        "label": "Yes",
        "video": "Yes.mp4",
        "poster": "yes_poster.jpg",
        "icon": "fa-check",
        "triggers": [
            # English
            "yes", "yeah", "yep", "sure", "correct", "right", "exactly",
            # Hindi
            "haan", "haa", "ha ji", "sahi hai", "bilkul",
            "हाँ", "हां", "हाँ जी", "सही है", "बिल्कुल",
            # Bengali
            "he", "haji", "thik", "ekdom", "shothik", "oboshshoi",
            "হ্যাঁ", "হ্যা", "একদম", "সঠিক", "অবশ্যই"
        ],
    },
    {
        "key": "no",
        "label": "No",
        "video": "No.mp4",
        "poster": "no_poster.jpg",
        "icon": "fa-xmark",
        "triggers": [
            # English
            "no", "nope", "nah", "not really", "incorrect", "wrong",
            # Hindi
            "nahi", "na", "nahin", "nahi ji", "galat", "bilkul nahi",
            "नहीं", "ना", "नही", "नहीं जी", "गलत", "बिल्कुल नहीं",
            # Bengali
            "noi", "bhul", "ekdom na", "kokhono na",
            "না", "নয়", "ভুল", "একদম না", "কখনো না"
        ],
    },
    {
        "key": "please_wait",
        "label": "Please wait",
        "video": "Please_Wait.mp4",
        "poster": "please_wait_poster.jpg",
        "icon": "fa-hourglass-half",
        "triggers": [
            # English
            "please wait", "wait", "wait a minute", "hold on", "one moment", "just a second",
            # Hindi
            "thoda ruko", "ruko", "intezar karo", "ek minute", "thoda intezar kijiye",
            "कृपया प्रतीक्षा करें", "रुको", "रुकिए", "थोड़ा रुको", "इंतजार करो", "एक मिनट",
            # Bengali
            "ektu darao", "darao", "ektu opekha korun", "opekkha koro", "ektu thamo",
            "একটু দাঁড়ান", "দাঁড়ান", "একটু অপেক্ষা করুন", "অপেক্ষা করুন", "একটু থামুন"
        ],
    },
    {
        "key": "understand",
        "label": "I understand",
        "video": "I_Understand.mp4",
        "poster": "i_understand_poster.jpg",
        "icon": "fa-circle-check",
        "triggers": [
            # English
            "i understand", "understand", "got it", "i get it", "understood", "makes sense",
            # Hindi
            "samajh gaya", "samajh gayi", "samajh aaya", "samajh gaye",
            "समझ गया", "समझ गई", "समझ गए", "समझ आ गया",
            # Bengali
            "bujhte perechi", "bujhechi", "bujhte parlam", "bujhe gechi",
            "বুঝতে পেরেছি", "বুঝেছি", "বুঝলাম", "বুঝতে পারলাম"
        ],
    },
    {
        "key": "repeat",
        "label": "Show that again?",
        "video": "Show_That_Again.mp4",
        "poster": "show_that_again_poster.jpg",
        "icon": "fa-rotate-left",
        "triggers": [
            # English
            "show that again", "can you repeat", "repeat that", "say that again", "once more", "show again",
            # Hindi
            "dobara dikhao", "phir se dikhao", "ek baar aur", "dobara batao", "phir se bolo",
            "दोबारा दिखाओ", "फिर से दिखाओ", "एक बार और", "दोबारा बताइए", "फिर से बोलो",
            # Bengali
            "abar dekhao", "aar ekbar", "arekbar dekhao", "abar bolo", "arekbar bolun",
            "আবার দেখাও", "আর একবার", "আরেকবার দেখাও", "আবার বলুন", "আবার বলো"
        ],
    },
    {
        "key": "thank_you",
        "label": "Thank you",
        "video": "Thank_You.mp4",
        "poster": "thank_you_poster.jpg",
        "icon": "fa-heart",
        "triggers": [
            # English
            "thank you", "thanks", "thank you so much", "many thanks",
            # Hindi
            "dhanyawad", "shukriya", "bahut dhanyawad", "bahut shukriya",
            "धन्यवाद", "शुक्रिया", "बहुत धन्यवाद", "बहुत शुक्रिया",
            # Bengali
            "dhonnobad", "onek dhonnobad", "dhonnobaad",
            "ধন্যবাদ", "অনেক ধন্যবাদ", "ধন্যবাদ আপনাকে"
        ],
    },
    {
        "key": "where_hurt",
        "label": "Where does it hurt?",
        "video": "Where_Does_It_Hurt.mp4",
        "poster": "where_does_it_hurt_poster.jpg",
        "icon": "fa-hand-holding-medical",
        "triggers": [
            # English
            "where does it hurt", "where is the pain", "where hurts", "tell me where it hurts", "which part hurts",
            # Hindi
            "kahan dard hai", "kaha dard ho raha hai", "dard kahan hai", "kahan taqleef hai",
            "कहाँ दर्द है", "कहाँ दर्द हो रहा है", "दर्द कहाँ है", "कहाँ तकलीफ है",
            # Bengali
            "kothay batha", "kothay batha korche", "batha kothay", "kothay lagche",
            "কোথায় ব্যথা", "কোথায় ব্যথা করছে", "ব্যথা কোথায়", "কোথায় লাগছে"
        ],
    },
    {
        "key": "are_you_ok",
        "label": "Are you ok?",
        "video": "Are_You_Ok.mp4",
        "poster": "are_you_ok_poster.jpg",
        "icon": "fa-circle-question",
        "triggers": [
            # English
            "are you ok", "are you alright", "are you feeling ok", "how are you feeling",
            # Hindi
            "kya aap theek ho", "aap theek ho", "aap theek hain na", "kya sab theek hai",
            "क्या आप ठीक हो", "आप ठीक हो", "आप ठीक हैं", "क्या आप ठीक हैं",
            # Bengali
            "apni kemon achen", "theek aachen", "apni thik achen to",
            "আপনি কেমন আছেন", "ঠিক আছেন", "আপনি ঠিক আছেন তো"
        ],
    },
    {
        # Pairs deliberately with the Stage 3 Emergency Detector -- this is
        # the reply a caregiver sends the moment they acknowledge an alert,
        # closing the loop instead of leaving the avatar disconnected from
        # the rest of the product.
        "key": "help_coming",
        "label": "Help is coming",
        "video": "Help_Is_Coming.mp4",
        "poster": "help_is_coming_poster.jpg",
        "icon": "fa-truck-medical",
        "triggers": [
            # English
            "help is coming", "help is on the way", "someone is coming", "don't worry help is coming",
            # Hindi
            "madad aa rahi hai", "chinta mat karo madad aa rahi hai", "sahayata aa rahi hai", "koi aa raha hai",
            "मदद आ रही है", "चिंता मत करो मदद आ रही है", "सहायता आ रही है", "कोई आ रहा है",
            # Bengali
            "shahajjo ashche", "help ashche", "chinta koro na shahajjo ashche", "keu ashche",
            "সাহায্য আসছে", "চিন্তা করবেন না সাহায্য আসছে", "সাহায্য পৌঁছাচ্ছে", "কেউ আসছে"
        ],
    },
    {
        # Pairs with the "Call Doctor" emergency trigger specifically.
        "key": "calling_doctor",
        "label": "Calling the doctor",
        "video": "Calling_The_Doctor.mp4",
        "poster": "calling_the_doctor_poster.jpg",
        "icon": "fa-user-doctor",
        "triggers": [
            # English
            "calling the doctor", "calling doctor", "i am calling the doctor", "call the doctor",
            # Hindi
            "doctor ko bula rahe hain", "doctor ko call kar rahe hain", "doctor aa rahe hain",
            "डॉक्टर को बुला रहे हैं", "डॉक्टर को कॉल कर रहे हैं", "डॉक्टर आ रहे हैं",
            # Bengali
            "doctor dakchi", "doctor ke dakchi", "daktar dakchi", "doctor ashchen",
            "ডাক্তার ডাকছি", "ডাক্তারকে ডাকছি", "ডাক্তার আসছেন", "ডাক্তার বাবুকে ডাকছি"
        ],
    },
]


def get_avatar_replies():
    """Returns the list with an `available` flag computed per entry, so
    templates never have to duplicate the "is this real" check."""
    return [
        {**r, "available": r["video"] is not None}
        for r in AVATAR_REPLIES
    ]
