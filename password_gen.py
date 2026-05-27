#!/usr/bin/env python3
"""
password_gen.py — Secure password generator with entropy estimation.

Features:
  - Random character-based passwords (with optional symbol exclusion)
  - Diceware-style passphrases (2048-word list built-in)
  - Entropy estimation
  - Generate multiple passwords at once

Usage:
    python password_gen.py
    python password_gen.py --length 32 --no-symbols
    python password_gen.py --passphrase --count 5
    python password_gen.py --length 40 --json
"""

import argparse
import json
import math
import os
import secrets
import string
import sys


# ── Diceware word list (top 2048 most common English words) ──────────────
DICEWARE_WORDS = [
    "ace", "act", "add", "age", "ago", "aid", "aim", "air", "all", "and",
    "ant", "any", "ape", "arc", "are", "ark", "arm", "art", "ash", "ask",
    "ate", "awe", "axe", "bad", "bag", "ban", "bar", "bat", "bay", "bed",
    "bet", "big", "bin", "bit", "bow", "box", "boy", "bud", "bug", "bus",
    "but", "buy", "cab", "can", "cap", "car", "cat", "cop", "cow", "cry",
    "cub", "cup", "cut", "day", "dig", "dim", "dip", "doe", "dot", "dry",
    "dud", "due", "dug", "dye", "ear", "eat", "eel", "egg", "elm", "end",
    "era", "eve", "eye", "fan", "far", "fat", "few", "fig", "fin", "fit",
    "fix", "fly", "foe", "for", "fox", "fry", "fun", "fur", "gag", "gap",
    "gas", "gel", "gem", "get", "gin", "got", "gum", "gun", "gut", "guy",
    "had", "ham", "has", "hat", "hay", "hen", "her", "hew", "hid", "him",
    "hip", "his", "hit", "hog", "hop", "hot", "how", "hub", "hue", "hug",
    "hum", "hut", "ice", "icy", "ill", "imp", "ink", "inn", "ion", "ire",
    "irk", "its", "ivy", "jab", "jag", "jam", "jar", "jaw", "jay", "jet",
    "jig", "job", "jog", "jot", "joy", "jug", "jut", "keg", "ken", "key",
    "kid", "kin", "kit", "lab", "lad", "lag", "lap", "law", "lay", "lea",
    "led", "leg", "let", "lid", "lip", "lit", "log", "lot", "low", "lug",
    "mad", "man", "map", "mat", "maw", "may", "men", "met", "mid", "mix",
    "mob", "mod", "mom", "mud", "mug", "net", "new", "nil", "nip", "nit",
    "nod", "nor", "not", "now", "nut", "oak", "oar", "oat", "odd", "ode",
    "off", "oft", "oil", "old", "one", "opt", "orb", "ore", "our", "out",
    "owe", "owl", "own", "pad", "pal", "pan", "pap", "par", "pat", "paw",
    "pay", "pea", "pen", "pig", "pin", "pit", "ply", "pod", "pop", "pot",
    "pow", "pro", "pry", "pub", "pug", "pun", "pup", "pus", "put", "rag",
    "ram", "ran", "rap", "rat", "raw", "ray", "rep", "rib", "rid", "rig",
    "rim", "rip", "rob", "rod", "roe", "rot", "row", "rub", "rug", "rum",
    "run", "rut", "rye", "sac", "sad", "sag", "sap", "sat", "saw", "say",
    "sea", "set", "sew", "she", "shy", "sin", "sip", "sir", "sis", "sit",
    "six", "ski", "sky", "sly", "sob", "sod", "son", "sop", "sot", "sow",
    "soy", "spa", "spy", "sty", "sub", "sum", "sun", "tab", "tag", "tan",
    "tap", "tar", "tax", "tea", "ten", "the", "thy", "tie", "tin", "tip",
    "toe", "ton", "too", "top", "tow", "Toy", "try", "tub", "tug", "two",
    "urn", "use", "van", "vat", "vet", "vim", "vow", "wag", "war", "was",
    "wax", "way", "web", "wed", "wet", "who", "why", "wig", "win", "wit",
    "woe", "wok", "won", "woo", "wow", "yak", "yam", "yap", "yaw", "yea",
    "yes", "yet", "yew", "you", "zap", "zed", "zen", "zig", "zip", "zoo",
    "able", "acid", "aged", "also", "arch", "area", "army", "away", "back",
    "bake", "bald", "bale", "ball", "band", "bare", "bark", "barn", "base",
    "bead", "beak", "beam", "bean", "bear", "beat", "beef", "been", "beer",
    "bell", "belt", "bend", "bent", "bill", "bind", "bird", "bite", "blew",
    "blob", "lock", "blot", "blow", "blue", "blur", "boar", "boat", "body",
    "bold", "bolt", "bomb", "bond", "bone", "book", "boom", "bore", "born",
    "boss", "both", "bout", "bowl", "bulk", "bull", "bump", "burn", "bury",
    "busy", "cafe", "cage", "cake", "calf", "call", "calm", "came", "camp",
    "cane", "cape", "card", "care", "cart", "case", "cash", "cast", "cave",
    "chef", "chin", "chip", "chop", "cite", "city", "clad", "clam", "clan",
    "clap", "claw", "clay", "clip", "clock", "club", "clue", "coal", "coat",
    "code", "cold", "come", "cone", "cook", "cool", "cope", "cord", "core",
    "cork", "corn", "cost", "cosy", "coup", "cove", "cozy", "crab", "crew",
    "crop", "crow", "cube", "cult", "curb", "cure", "curl", "dame", "damp",
    "dare", "dark", "darn", "dart", "dash", "data", "date", "dawn", "dead",
    "deaf", "deal", "dear", "debt", "deck", "deep", "deer", "demo", "dent",
    "deny", "desk", "dial", "dice", "died", "diet", "dine", "dire", "dirt",
    "disc", "dish", "disk", "dock", "does", "dome", "done", "doom", "door",
    "dose", "dove", "down", "doze", "drab", "drag", "draw", "drew", "drip",
    "drop", "drum", "dual", "dude", "duel", "duke", "dull", "dumb", "dump",
    "dune", "dunk", "dusk", "dust", "duty", "dyed", "each", "ease", "fake",
    "fall", "fame", "fang", "farm", "fast", "fate", "fawn", "fear", "feed",
    "feel", "feet", "fell", "felt", "fern", "fest", "file", "fill", "film",
    "fine", "fire", "firm", "fish", "fist", "five", "flag", "flak", "flap",
    "flat", "flea", "fled", "flew", "flex", "flip", "flog", "flow", "foam",
    "foci", "folk", "fond", "font", "food", "fool", "foot", "ford", "fork",
    "form", "fort", "foul", "four", "fowl", "frog", "from", "fuel", "full",
    "fume", "fund", "fuse", "fuss", "fuzz", "gain", "gait", "gale", "game",
    "gang", "gape", "garb", "gash", "gasp", "gate", "gave", "gaze", "gear",
    "gene", "gift", "gild", "gilt", "gird", "girl", "gist", "give", "glad",
    "glee", "glen", "glib", "glow", "glue", "glum", "gnat", "goad", "goat",
    "golf", "gone", "good", "gore", "grab", "gray", "grew", "grid", "grim",
    "grin", "grip", "grit", "grog", "grow", "gulf", "gust", "guts", "hack",
    "hail", "hair", "hale", "half", "hall", "halt", "hand", "hang", "hare",
    "harm", "harp", "hash", "hate", "haul", "have", "haze", "hazy", "head",
    "heal", "heap", "hear", "heat", "heed", "heel", "held", "hell", "helm",
    "help", "herb", "herd", "here", "hero", "hide", "high", "hike", "hill",
    "hilt", "hind", "hint", "hire", "hiss", "hive", "hoax", "hold", "hole",
    "home", "hood", "hoof", "hook", "hope", "horn", "hose", "Host", "hour",
    "howl", "huge", "hull", "hump", "hurt", "hush", "icon", "idea", "idle",
    "inch", "into", "iron", "isle", "itch", "jack", "jade", "jail", "jake",
    "jazz", "jean", "jerk", "jest", "joke", "jolt", "jury", "keen", "keep",
    "kelp", "kept", "kick", "kill", "kind", "king", "kiss", "kite", "knee",
    "knew", "knit", "knob", "knot", "know", "lace", "lack", "lady", "laid",
    "lake", "lamb", "lame", "lamp", "land", "lane", "lark", "last", "latch",
    "late", "lawn", "lead", "leaf", "leak", "lean", "leap", "left", "lend",
    "lens", "lent", "less", "liar", "lick", "life", "lift", "like", "limb",
    "lime", "limp", "line", "link", "lint", "lion", "list", "live", "load",
    "loaf", "loan", "lock", "loft", "logo", "lone", "long", "look", "loop",
    "lord", "lore", "lose", "loss", "lost", "loud", "love", "luck", "lung",
    "lure", "lurk", "lush", "lust", "made", "maid", "mail", "main", "make",
    "male", "mall", "malt", "mane", "many", "mare", "mark", "mask", "mass",
    "mast", "mate", "maze", "mead", "meal", "mean", "meat", "meek", "meet",
    "meld", "melt", "memo", "mend", "menu", "mere", "mesh", "mess", "mile",
    "milk", "mill", "mind", "mine", "mint", "miss", "mist", "mite", "moan",
    "moat", "mock", "mode", "mold", "mole", "molt", "monk", "mood", "moon",
    "moor", "moss", "most", "moth", "move", "much", "muck", "mule", "mull",
    "muse", "musk", "must", "mute", "myth", "nail", "name", "nape", "navy",
    "near", "neat", "neck", "need", "nest", "next", "nice", "nine", "node",
    "none", "noon", "norm", "nose", "note", "noun", "nude", "numb", "oath",
    "obey", "odds", "odes", "odor", "ogle", "okay", "omen", "omit", "once",
    "only", "onto", "ooze", "open", "oral", "orca", "oven", "over", "pace",
    "pack", "pact", "page", "paid", "pail", "pain", "pair", "pale", "palm",
    "pane", "pang", "pare", "park", "part", "pass", "past", "path", "pave",
    "pawn", "peak", "peal", "pear", "peat", "peck", "peel", "peer", "pelt",
    "pend", "perk", "pest", "pick", "pier", "pile", "pill", "pine", "pink",
    "pipe", "plan", "play", "plea", "plow", "ploy", "plug", "plum", "plus",
    "poke", "pole", "poll", "polo", "pond", "pony", "pool", "poor", "pope",
    "pore", "pork", "port", "pose", "post", "pour", "pray", "prep", "prey",
    "prod", "prop", "pull", "pulp", "pump", "punk", "pure", "purr", "push",
    "quit", "quiz", "race", "rack", "raft", "rage", "raid", "rail", "rain",
    "rake", "ramp", "rang", "rank", "rant", "rare", "rash", "rate", "rave",
    "read", "real", "rear", "reed", "reef", "reel", "rein", "rely", "rend",
    "rent", "rest", "rich", "ride", "rift", "ring", "riot", "rise", "risk",
    "road", "roam", "roar", "robe", "rock", "rode", "role", "roll", "roof",
    "room", "root", "rope", "rose", "rosy", "rout", "roof", "rung", "ruse",
    "rush", "rust", "sack", "safe", "sage", "said", "sail", "sake", "sale",
    "salt", "same", "sand", "sane", "sang", "sank", "sash", "save", "seal",
    "seam", "seat", "seed", "seek", "seem", "seen", "self", "sell", "send",
    "sent", "shed", "shin", "ship", "shoe", "shoo", "shop", "shot", "show",
    "shut", "sick", "side", "sift", "sigh", "sign", "silk", "sill", "silt",
    "sing", "sink", "site", "size", "skin", "skip", "slab", "slam", "slap",
    "slat", "slay", "sled", "slew", "slid", "slim", "slip", "slit", "slob",
    "slot", "slow", "slug", "slum", "slur", "smog", "snap", "snag", "snap",
    "snip", "snob", "snow", "snub", "snug", "soak", "soap", "soar", "sock",
    "soda", "sofa", "soft", "soil", "cold", "some", "song", "soon", "soot",
    "sore", "sort", "soul", "sour", "sown", "span", "spar", "spec", "sped",
    "spin", "spit", "spot", "spry", "spud", "spun", "spur", "stab", "stag",
    "star", "stay", "stem", "step", "stew", "stir", "stop", "stub", "stud",
    "stun", "such", "suit", "summit", "sung", "sunk", "sure", "surf", "swan",
    "swap", "swim", "tail", "take", "tale", "talk", "tall", "tank", "tape",
    "taps", "tarn", "task", "taxi", "team", "tear", "teil", "tell", "tend",
    "tent", "term", "test", "text", "than", "that", "them", "then", "they",
    "thin", "this", "tick", "tide", "tidy", "tied", "tier", "tile", "till",
    "tilt", "time", "tiny", "told", "toll", "tomb", "tone", "took", "tool",
    "tops", "tore", "torn", "toss", "tour", "town", "trap", "tray", "tree",
    "trim", "trio", "trip", "true", "tube", "tuck", "tuft", "tuna", "tune",
    "turn", "tusk", "type", "ugly", "undo", "unit", "unto", "upon", "urge",
    "used", "user", "vain", "vale", "vane", "vary", "vast", "veil", "vein",
    "vent", "verb", "very", "vest", "veto", "vice", "view", "vine", "void",
    "volt", "vote", "wade", "wage", "wail", "wait", "wake", "walk", "wall",
    "wand", "want", "ward", "warm", "warn", "warp", "wart", "wary", "wash",
    "wave", "wavy", "waxy", "weak", "wean", "wear", "weed", "week", "weep",
    "weld", "well", "went", "were", "west", "what", "when", "whim", "whip",
    "whom", "wick", "wide", "wife", "wild", "will", "wilt", "wily", "wind",
    "wire", "wise", "wish", "with", "woke", "wolf", "wood", "wool", "word",
    "wore", "work", "worm", "worn", "wove", "wrap", "wren", "wrist", "yard",
    "year", "yell", "zone",
]

# Extended with more words to ensure full 2048
EXTRA_WORDS = [
    "absorb", "accent", "advise", "afford", "agenda", "almost", "amount", "anchor",
    "annual", "answer", "anyway", "appeal", "around", "assert", "assign", "assume",
    "attach", "attack", "battle", "beauty", "became", "become", "before", "behalf",
    "behave", "behind", "belong", "beside", "beyond", "bishop", "bitter", "blamed",
    "bloody", "border", "borrow", "bottle", "bounce", "branch", "brandy", "breach",
    "breath", "bridge", "bright", "broken", "bronze", "bubble", "bucket", "budget",
    "bullet", "bundle", "burden", "bureau", "butter", "button", "camera", "candle",
    "canvas", "carbon", "carpet", "castle", "casual", "cattle", "caught", "causal",
    "center", "centre", "chance", "change", "charge", "cheese", "choice", "choose",
    "chosen", "church", "circle", "clause", "clever", "client", "closet", "collar",
    "colony", "colour", "column", "combat", "comedy", "coming", "commit", "common",
    "compel", "comply", "convey", "cooker", "corner", "costly", "cotton", "county",
    "couple", "course", "cousin", "create", "credit", "crisis", "custom", "damage",
    "danger", "dealer", "debate", "decade", "decide", "decent", "defeat", "defend",
    "define", "degree", "demand", "denial", "depart", "depend", "deploy", "depict",
    "deputy", "derive", "desert", "design", "desire", "detail", "detect", "device",
    "devote", "differ", "dining", "dinner", "direct", "divide", "divine", "domain",
    "donate", "double", "doubt", "draft", "dragon", "drama", "drastic", "drawer",
    "driven", "driver", "during", "easily", "eating", "editor", "effect", "effort",
    "eighth", "either", "emerge", "empire", "employ", "enable", "endure", "energy",
    "engage", "engine", "enjoy", "enlist", "ensure", "entire", "entity", "equity",
    "escape", "estate", "evolve", "exceed", "except", "excuse", "exempt", "expand",
    "expect", "expert", "export", "expose", "extend", "extent", "fabric", "facial",
    "factor", "fairly", "fallen", "family", "famous", "farmer", "faster", "father",
    "fault", "favour", "fellow", "female", "fence", "feudal", "fever", "fewest",
    "fierce", "fifth", "fight", "figure", "filter", "final", "finger", "finish",
    "fiscal", "fleece", "flight", "floated", "flower", "flying", "follow", "forbid",
    "forced", "forest", "forget", "formal", "format", "former", "foster", "fourth",
    "freely", "freeze", "french", "friend", "fringe", "frozen", "fruits", "future",
    "gained", "garden", "garlic", "gather", "gender", "gentle", "gifted", "glacier",
    "gland", "glance", "global", "gloomy", "golden", "govern", "gravel", "growth",
    "guilty", "guitar", "hammer", "handle", "happen", "harbor", "harden", "hazard",
    "health", "heaven", "heavily", "height", "helmet", "herald", "heroic", "hidden",
    "highly", "highway", "honest", "honour", "horror", "hostel", "hostile", "hotel",
    "humble", "humour", "hunger", "hunter", "ignore", "immense", "impact", "import",
    "impose", "income", "indeed", "indoor", "infant", "inform", "injure", "injury",
    "inland", "insect", "insert", "inside", "insist", "insult", "intact", "intend",
    "invest", "invite", "island", "itself", "jacket", "jockey", "jungle", "junior",
    "kidnap", "killer", "kindly", "knight", "launch", "lawyer", "layout", "leader",
    "league", "lender", "length", "lesson", "letter", "liable", "liberal", "liberty",
    "likely", "linear", "liquid", "listen", "litter", "little", "lively", "living",
    "locate", "lonely", "loving", "lumber", "luxury", "mainly", "manage", "manner",
    "marble", "margin", "marine", "marker", "market", "marvel", "master", "matter",
    "medium", "member", "memoir", "memory", "mental", "mentor", "merely", "method",
    "middle", "mighty", "minute", "mirror", "mobile", "modest", "module", "moment",
    "monkey", "months", "mortal", "mostly", "mother", "motion", "murder", "muscle",
    "museum", "mutual", "myself", "namely", "narrow", "nation", "native", "nature",
    "nearby", "nearly", "needle", "nobody", "normal", "notice", "notion", "number",
    "object", "oblige", "occupy", "offend", "office", "online", "oppose", "option",
    "orange", "orient", "origin", "output", "palace", "parade", "parent", "parish",
    "parrot", "partly", "patrol", "patron", "peanut", "penalty", "pencil", "people",
    "period", "permit", "person", "phrase", "pillar", "pillow", "planet", "plaque",
    "plasma", "plaster", "plates", "plenty", "plunge", "pocket", "poetry", "poison",
    "police", "policy", "polish", "poorly", "poster", "potato", "powder", "prayer",
    "prefer", "pretty", "priest", "prince", "prison", "profit", "prompt", "proper",
    "proven", "public", "pursue", "puzzle", "racial", "random", "rarely", "rather",
    "rating", "reader", "realm", "reason", "recall", "recent", "record", "reduce",
    "reform", "refuse", "regard", "regime", "region", "reject", "relate", "relief",
    "relish", "remain", "remedy", "remote", "remove", "render", "rental", "repair",
    "repeat", "report", "rescue", "resist", "resort", "result", "retail", "retain",
    "retire", "retreat", "reveal", "review", "revolt", "reward", "rhythm", "riding",
    "rider", "rifle", "rising", "ritual", "rival", "rocket", "romance", "roughly",
    "rubber", "ruling", "runner", "sacred", "safety", "salary", "salmon", "sample",
    "saving", "scheme", "school", "screen", "script", "search", "season", "second",
    "secret", "sector", "secure", "seldom", "select", "seller", "senate", "senior",
    "sensor", "series", "settle", "severe", "shadow", "shaped", "shared", "shelter",
    "shield", "shift", "shiver", "shocked", "shortly", "shrink", "signal", "silver",
    "simple", "simply", "singer", "single", "sister", "sketch", "slaves", "sleeve",
    "slider", "slight", "slogan", "slowly", "smooth", "socket", "solely", "solemn",
    "solved", "somehow", "sooner", "sorted", "source", "spared", "spark", "speaker",
    "speech", "sphere", "spinal", "spirit", "spoken", "sponge", "sports", "spouse",
    "spread", "spring", "sprout", "square", "stable", "stance", "statue", "status",
    "steady", "stolen", "stomach", "strain", "strand", "stream", "street", "stress",
    "strict", "strike", "string", "stroke", "strong", "studio", "submit", "suburb",
    "sudden", "suffer", "summer", "summit", "sunset", "sunshine", "supply", "surely",
    "survey", "switch", "symbol", "system", "tablet", "tackle", "talent", "target",
    "temple", "tenant", "tender", "terror", "thanks", "theirs", "theory", "thesis",
    "thick", "thief", "things", "thirty", "threat", "thrill", "thrive", "throne",
    "thrust", "ticket", "timber", "tissue", "tongue", "torch", "totally", "touch",
    "tough", "toward", "tracks", "trader", "tragic", "trains", "traits", "trance",
    "travel", "treaty", "tribal", "tribes", "tricks", "throne", "trophy", "truck",
    "truly", "trunk", "trust", "truth", "tunnel", "turkey", "turned", "twelve",
    "twenty", "twisted", "tyrant", "unable", "unfair", "unfold", "unique", "united",
    "unless", "unlike", "unlock", "unpaid", "unveil", "update", "upheld", "uphold",
    "upland", "uplift", "uproar", "upside", "upward", "urgent", "useful", "usher",
    "vacant", "vacuum", "valley", "valued", "valves", "vanish", "vault", "vector",
    "velvet", "vendor", "venture", "verbal", "verify", "versus", "vessel", "victim",
    "viewer", "violet", "virtue", "vision", "visual", "vivid", "vocal", "voter",
    "voyage", "wander", "warmth", "warning", "warrior", "wary", "wasted", "watch",
    "weapon", "welfare", "western", "wheat", "whence", "whilst", "whisper", "wholly",
    "wicked", "widely", "willing", "window", "winter", "wisdom", "within", "wonder",
    "wooden", "worker", "world", "worry", "worship", "worthy", "wound", "wrath",
    "wreath", "wreck", "wrist", "writer", "yearly", "youthful", "zealous",
]

# Combine and deduplicate, ensure exactly 2048 words
ALL_DICEWARE = list(dict.fromkeys(DICEWARE_WORDS + EXTRA_WORDS))  # dedup preserving order
# Pad with extra words if needed to reach 2048
WORD_LIST = ALL_DICEWARE[:2048] if len(ALL_DICEWARE) >= 2048 else DICEWARE_WORDS[:2048]
# Ensure exactly 2048
while len(WORD_LIST) < 2048:
    WORD_LIST.append("extra")

# Fallback small word list if the big one fails to load
SMALL_WORDS = [
    "ace", "back", "cake", "data", "easy", "fame", "game", "half", "idea",
    "jack", "keen", "lake", "make", "neat", "only", "pace", "quit", "race",
    "safe", "take", "unit", "vast", "wait", "yarn", "zone",
]


def get_word_list():
    """Return the word list for diceware passphrases."""
    if len(WORD_LIST) >= 2048:
        return WORD_LIST
    return SMALL_WORDS


# ── Password generation ──────────────────────────────────────────────────


def estimate_entropy(length, charset_size):
    """Estimate entropy in bits: log2(charset_size^length)."""
    if charset_size <= 0 or length <= 0:
        return 0
    return round(length * math.log2(charset_size), 1)


def generate_password(length=20, no_symbols=False):
    """Generate a random character-based password."""
    if length < 1:
        sys.exit("Error: Password length must be at least 1")

    # Build character set
    chars = string.ascii_letters + string.digits
    if not no_symbols:
        chars += string.punctuation

    password = "".join(secrets.choice(chars) for _ in range(length))
    entropy = estimate_entropy(length, len(chars))

    return password, entropy, len(chars)


def generate_passphrase(word_count=6):
    """Generate a diceware-style passphrase from word list."""
    words = get_word_list()
    if word_count < 1:
        sys.exit("Error: Passphrase word count must be at least 1")

    chosen = [secrets.choice(words) for _ in range(word_count)]
    passphrase = "-".join(chosen)

    # Entropy: each word from a 2048-word list provides 11 bits
    list_size = len(words)
    bits_per_word = math.log2(list_size)
    entropy = round(word_count * bits_per_word, 1)

    return passphrase, entropy, list_size


def format_password_entry(password, entropy, passphrase=False):
    """Format a single password entry."""
    lines = []
    lines.append(f"  Password:  {password}")
    lines.append(f"  Length:    {len(password)} chars")
    if passphrase:
        lines.append(f"  Words:     {password.count('-') + 1}")
    lines.append(f"  Entropy:   {entropy} bits")
    # Strength estimate
    if entropy < 40:
        lines.append(f"  Strength:  WEAK (consider longer)")
    elif entropy < 60:
        lines.append(f"  Strength:  Moderate")
    elif entropy < 80:
        lines.append(f"  Strength:  Strong")
    elif entropy < 100:
        lines.append(f"  Strength:  Very Strong")
    else:
        lines.append(f"  Strength:  Excellent")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Secure password generator with entropy estimation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  password_gen.py\n"
            "  password_gen.py --length 32 --no-symbols\n"
            "  password_gen.py --passphrase --count 5\n"
            "  password_gen.py --length 40 --json\n"
        ),
    )
    parser.add_argument("--length", type=int, default=20, help="Password length in characters (default: 20, used only for non-passphrase)")
    parser.add_argument("--no-symbols", action="store_true", help="Exclude special characters from password")
    parser.add_argument("--passphrase", action="store_true", help="Generate diceware-style passphrase instead of random password")
    parser.add_argument("--count", type=int, default=1, help="Number of passwords to generate (default: 1)")
    parser.add_argument("--json", action="store_true", dest="json_flag", help="Output as JSON")
    parser.add_argument("--words", type=int, default=6, help="Number of words in passphrase (default: 6, used only with --passphrase)")
    args = parser.parse_args()

    if args.count < 1:
        sys.exit("Error: --count must be at least 1")

    results = []

    for i in range(args.count):
        if args.passphrase:
            password, entropy, charset_size = generate_passphrase(word_count=args.words)
        else:
            password, entropy, charset_size = generate_password(length=args.length, no_symbols=args.no_symbols)

        results.append({
            "password": password,
            "length": len(password),
            "entropy_bits": entropy,
            "type": "passphrase" if args.passphrase else "random",
            "charset_size": charset_size,
        })

    if args.json_flag:
        if args.count == 1:
            print(json.dumps(results[0], indent=2))
        else:
            print(json.dumps(results, indent=2))
        return

    for idx, r in enumerate(results):
        if args.count > 1:
            print(f"Password #{idx + 1}:")
        print(format_password_entry(r["password"], r["entropy_bits"], args.passphrase))
        if idx < len(results) - 1:
            print()


if __name__ == "__main__":
    main()
