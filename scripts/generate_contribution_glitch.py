import json
import os
import random
import urllib.request


GITHUB_API = "https://api.github.com/graphql"
OUTPUT_FILE = "contribution-glitch.svg"

TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN não encontrado.")


QUERY = """
query {
  viewer {
    login
    contributionsCollection(
      from: "2025-09-22T00:00:00Z"
      to: "2026-09-22T23:59:59Z"
    ) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""


def github_graphql(query):
    data = json.dumps({"query": query}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "jguilhermemiranda-contribution-glitch",
    }

    last_error = None

    for attempt in range(MAX_GRAPHQL_ATTEMPTS):
        request = urllib.request.Request(
            GITHUB_API,
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"GitHub GraphQL HTTP {error.code}: {body}"
            )
            if error.code not in {429, 500, 502, 503, 504}:
                raise last_error from error

        except urllib.error.URLError as error:
            last_error = RuntimeError(
                f"Erro de conexão com GitHub GraphQL: {error}"
            )

        else:
            if "errors" not in result:
                if "data" not in result or "viewer" not in result["data"]:
                    raise RuntimeError(
                        "Resposta inesperada da API:\n"
                        + json.dumps(result, indent=2)
                    )

                return result["data"]["viewer"]

            last_error = RuntimeError(
                "GitHub GraphQL retornou erros:\n"
                + json.dumps(result["errors"], indent=2)
            )

        if attempt < MAX_GRAPHQL_ATTEMPTS - 1:
            time.sleep(2 ** attempt)

    raise last_error


def contribution_level(count, maximum):
    if count == 0:
        return 0

    if maximum <= 0:
        return 0

    ratio = count / maximum

    if ratio <= 0.25:
        return 1

    if ratio <= 0.50:
        return 2

    if ratio <= 0.75:
        return 3

    return 4


def generate_svg(calendar):
    weeks = calendar["weeks"]

    cell_size = 12
    gap = 3

    width = len(weeks) * (cell_size + gap) + 30
    height = 7 * (cell_size + gap) + 30

    colors = {
        0: "#161b22",
        1: "#3B176D",
        2: "#5B21B6",
        3: "#7C3AED",
        4: "#A78BFA",
    }

    all_days = []

    for week in weeks:
        for day in week["contributionDays"]:
            all_days.append(day)

    maximum = max(
        (day["contributionCount"] for day in all_days),
        default=1,
    )

    svg = []

    svg.append(
        f'''<svg xmlns="http://www.w3.org/2000/svg"
        width="{width}"
        height="{height}"
        viewBox="0 0 {width} {height}">'''
    )

    svg.append("""
    <defs>

      <filter id="glow">
        <feGaussianBlur stdDeviation="1.5" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>

      <pattern
        id="scanlines"
        width="100%"
        height="6"
        patternUnits="userSpaceOnUse">

        <line
          x1="0"
          y1="0"
          x2="100%"
          y2="0"
          stroke="#A78BFA"
          stroke-opacity="0.035"
          stroke-width="1"/>

      </pattern>

    </defs>
    """)

    # Background
    svg.append(
        f'<rect width="{width}" height="{height}" '
        f'rx="8" fill="#0d1117"/>'
    )

    random.seed(2026)

    # Contribution cells
    for week_index, week in enumerate(weeks):

        for day in week["contributionDays"]:

            weekday = day["weekday"]
            count = day["contributionCount"]

            level = contribution_level(count, maximum)
            color = colors[level]

            x = 10 + week_index * (cell_size + gap)
            y = 10 + weekday * (cell_size + gap)

            svg.append(
                f'''
                <rect
                  x="{x}"
                  y="{y}"
                  width="{cell_size}"
                  height="{cell_size}"
                  rx="2"
                  fill="{color}"
                  data-date="{day["date"]}"
                  data-count="{count}">
                </rect>
                '''
            )

    # Glitch overlay
    glitch_cells = []

    for week_index, week in enumerate(weeks):

        for day in week["contributionDays"]:

            # Only some cells participate in the glitch.
            if random.random() > 0.055:
                continue

            weekday = day["weekday"]
            count = day["contributionCount"]

            level = contribution_level(count, maximum)

            if level == 0:
                continue

            color = colors[level]

            x = 10 + week_index * (cell_size + gap)
            y = 10 + weekday * (cell_size + gap)

            glitch_cells.append((x, y, color))

    svg.append(
        '<g filter="url(#glow)" opacity="0.85">'
    )

    for index, (x, y, color) in enumerate(glitch_cells):

        # Different timing for every glitch fragment
        delay = (index % 17) * 0.17

        svg.append(
            f'''
            <rect
              x="{x}"
              y="{y}"
              width="{cell_size}"
              height="{cell_size}"
              rx="2"
              fill="{color}">

              <animateTransform
                attributeName="transform"
                type="translate"
                values="
                  0 0;
                  0 0;
                  7 0;
                  -4 0;
                  2 0;
                  0 0;
                  0 0"
                keyTimes="
                  0;
                  0.45;
                  0.48;
                  0.51;
                  0.54;
                  0.60;
                  1"
                dur="3.7s"
                begin="{delay:.2f}s"
                repeatCount="indefinite"/>

              <animate
                attributeName="opacity"
                values="0;0;0.9;0.45;1;0"
                keyTimes="0;0.44;0.48;0.52;0.58;0.65"
                dur="3.7s"
                begin="{delay:.2f}s"
                repeatCount="indefinite"/>

            </rect>
            '''
        )

    svg.append("</g>")

    # Horizontal glitch bars
    svg.append("""
    <g>

      <rect
        x="0"
        y="25"
        width="100%"
        height="2"
        fill="#A78BFA"
        opacity="0">

        <animate
          attributeName="opacity"
          values="0;0;0.55;0;0;0"
          dur="4.2s"
          repeatCount="indefinite"/>

        <animate
          attributeName="y"
          values="25;25;70;110;45;25"
          dur="4.2s"
          repeatCount="indefinite"/>

      </rect>

      <rect
        x="0"
        y="80"
        width="100%"
        height="1"
        fill="#8B5CF6"
        opacity="0">

        <animate
          attributeName="opacity"
          values="0;0.7;0;0;0.5;0"
          dur="2.8s"
          repeatCount="indefinite"/>

      </rect>

    </g>
    """)

    # Scanlines
    svg.append(
        f'<rect width="{width}" height="{height}" '
        f'fill="url(#scanlines)" pointer-events="none"/>'
    )

    svg.append("</svg>")

    return "\n".join(svg)


def main():
    viewer = github_graphql(QUERY)

    calendar = (
        viewer["contributionsCollection"]
        ["contributionCalendar"]
    )

    svg = generate_svg(calendar)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(svg)

    print(
        f"Contribution graph generated for "
        f"@{viewer['login']}"
    )

    print(
        f"Total contributions: "
        f"{calendar['totalContributions']}"
    )


if __name__ == "__main__":
    main()