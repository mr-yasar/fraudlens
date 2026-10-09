from calibrate_9pages_target import test_config
from pathlib import Path

configs = [
    (9.62, 1.172, 16.5, 17, 82),
    (9.65, 1.175, 16.5, 17, 82),
    (9.68, 1.178, 16.5, 17, 82),
    (9.70, 1.180, 17, 17.5, 82),
    (9.72, 1.182, 17, 17.5, 80),
]

for cfg in configs:
    pages, p9_chars, html_mod = test_config(*cfg)
    if pages == 9 and p9_chars >= 4000:
        print(f"Optimal balance: Pages={pages}, P9_chars={p9_chars}")
        target_html = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/FraudLens_AI_IEEE_Research_Paper.html")
        with open(target_html, "w", encoding="utf-8") as f:
            f.write(html_mod)
        break
