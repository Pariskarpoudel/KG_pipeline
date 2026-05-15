SYSTEM_PROMPT = """You are an expert knowledge graph constructor. Your task is to extract factual information from the provided text and represent it strictly as a JSON array of knowledge graph triples.

### Output Format
- The output must be a JSON array.
- Each element must be a JSON object with exactly three non-empty keys:
  - "subject": a noun phrase representing an entity
  - "relation": a concise verb or phrase (e.g., "discovered", "born in", "awarded prize", "is a")
  - "object": a noun phrase representing an entity, value, or date

### Constraints
- Extract all MEANINGFUL and RELEVANT triples — skip trivial, vague, or redundant facts.
- All keys must exist and all values must be non-empty strings.
- Subject and object must be noun phrases — never pronouns, generic words, scores, counts, or descriptive phrases.
- Never use compound subjects or objects like "X and Y" — split into separate triples.
- Never extract the same fact in both directions.
- If no triples can be extracted, return exactly: []
"""

def build_user_prompt(article_title: str, section_heading: str, chunk_text: str) -> str:
    return f"""Article: {article_title}
Section: {section_heading}

Examples:
Text: "Marie Curie discovered Polonium in 1898 while working in Paris."
Output:[
        {{"subject": "Marie Curie", "relation": "discovered", "object": "Polonium"}},
        {{"subject": "Polonium", "relation": "discovery year", "object": "1898"}},
        {{"subject": "Marie Curie", "relation": "worked in", "object": "Paris"}}
    ]

Text: "The iPhone is a line of smartphones produced by Apple Inc. that runs on the iOS operating system. The first iPhone was announced by Steve Jobs on January 9, 2007 at the Macworld conference in San Francisco and released in the United States on June 29, 2007. It introduced a multi-touch interface, virtual keyboard, and integration of internet services including Safari web browser, email, and the iPod music player in a single device. The original iPhone popularized the modern smartphone era and significantly influenced subsequent mobile phone designs. Apple has released new iPhone models annually, each bringing hardware and software advancements. The iPhone 3G (2008) added 3G connectivity and launched the App Store. The iPhone 4 (2010) featured a Retina display and front-facing camera. The iPhone 5s (2013) introduced Touch ID fingerprint sensor. The iPhone X (2017) removed the home button, added Face ID facial recognition, and introduced an edge-to-edge OLED screen. More recent models such as the iPhone 12 series (2020) brought 5G support, while the iPhone 14 Pro (2022) added the Dynamic Island interface and always-on display. As of 2024, cumulative iPhone sales exceed 2.3 billion units worldwide, making it the best-selling smartphone line in history."
Output:[
        {{"subject": "iPhone", "relation": "is a", "object": "line of smartphones"}},
        {{"subject": "iPhone", "relation": "produced by", "object": "Apple Inc."}},
        {{"subject": "iPhone", "relation": "runs on", "object": "iOS"}},
        {{"subject": "first iPhone", "relation": "announced by", "object": "Steve Jobs"}},
        {{"subject": "first iPhone", "relation": "announced on", "object": "January 9, 2007"}},
        {{"subject": "first iPhone", "relation": "announced at", "object": "Macworld conference"}},
        {{"subject": "Macworld conference", "relation": "located in", "object": "San Francisco"}},
        {{"subject": "first iPhone", "relation": "released on", "object": "June 29, 2007"}},
        {{"subject": "first iPhone", "relation": "released in", "object": "United States"}},
        {{"subject": "iPhone 3G", "relation": "released in", "object": "2008"}},
        {{"subject": "iPhone 3G", "relation": "added", "object": "App Store"}},
        {{"subject": "iPhone 4", "relation": "released in", "object": "2010"}},
        {{"subject": "iPhone 4", "relation": "introduced", "object": "Retina display"}},
        {{"subject": "iPhone X", "relation": "released in", "object": "2017"}},
        {{"subject": "iPhone X", "relation": "introduced", "object": "Face ID"}},
        {{"subject": "iPhone", "relation": "has cumulative sales of", "object": "over 2.3 billion units worldwide"}},
        {{"subject": "iPhone", "relation": "is", "object": "the best-selling smartphone line in history"}}
    ]


Now please extract triplets from the following text:
Text: "{chunk_text}"
Output:"""