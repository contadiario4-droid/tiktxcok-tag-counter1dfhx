
def normalize_apify_video(video, source):
    """Converte formatos comuns de saída do Actor para o painel."""
    if not isinstance(video, dict):
        return None

    stats = video.get("stats") or video.get("statistics") or {}
    author = video.get("author") or video.get("authorMeta") or video.get("author_info") or {}

    def first(*values, default=""):
        for value in values:
            if value is not None and value != "":
                return value
        return default

    username = first(
        author.get("unique_id") if isinstance(author, dict) else None,
        author.get("name") if isinstance(author, dict) else None,
        video.get("authorName"),
        video.get("username"),
        video.get("author"),
        default="desconhecido",
    )
    if isinstance(username, dict):
        username = username.get("unique_id") or username.get("name") or "desconhecido"

    views = first(video.get("playCount"), video.get("play_count"),
                  video.get("views"), stats.get("playCount"),
                  stats.get("play_count"), default=0)
    likes = first(video.get("diggCount"), video.get("digg_count"),
                  video.get("likes"), stats.get("diggCount"),
                  stats.get("digg_count"), default=0)
    comments = first(video.get("commentCount"), video.get("comment_count"),
                     video.get("comments"), stats.get("commentCount"),
                     stats.get("comment_count"), default=0)
    shares = first(video.get("shareCount"), video.get("share_count"),
                   video.get("shares"), stats.get("shareCount"),
                   stats.get("share_count"), default=0)

    def as_int(value):
        try:
            return int(value or 0)
        except (ValueError, TypeError):
            return 0

    video_id = str(first(video.get("id"), video.get("videoId"),
                         video.get("aweme_id"), default=""))
    link = first(
        video.get("webVideoUrl"),
        video.get("video_url"),
        video.get("url"),
        default="",
    )
    if not link and video_id:
        link = f"https://www.tiktok.com/@{str(username).lstrip('@')}/video/{video_id}"

    description = first(
        video.get("text"), video.get("desc"),
        video.get("description"), default=""
    )
    created = first(video.get("createTime"), video.get("create_time"),
                    video.get("createTimeISO"), default="")
    created_at = str(created)
    try:
        if isinstance(created, (int, float)) or str(created).isdigit():
            stamp = float(created)
            if stamp > 10**12:
                stamp /= 1000
            created_at = datetime.fromtimestamp(
                stamp, tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError, OSError, OverflowError):
        pass

    v, l, c, s = map(as_int, (views, likes, comments, shares))
    engagement = (l + c + s) / v * 100 if v else 0

    return {
        "Origem": source,
        "Perfil": str(username).lstrip("@"),
        "Legenda": str(description),
        "Data do vídeo": created_at,
        "Visualizações": v,
        "Curtidas": l,
        "Comentários": c,
        "Compartilhamentos": s,
        "Engajamento (%)": round(engagement, 2),
        "Link": link,
    }


def collect_tiktok(username, hashtag, max_items, ms_token=""):
    """Executa o Actor da Apify para perfil e hashtag."""
    token = st.secrets.get("APIFY_API_TOKEN", "")
    if not token:
        raise RuntimeError(
            "Token da Apify não encontrado. Configure APIFY_API_TOKEN "
            "em Settings > Secrets no Streamlit."
        )

    endpoint = (
        "https://api.apify.com/v2/actors/"
        "xtdata~tiktok-scraper/run-sync-get-dataset-items"
    )
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    errors = []

    jobs = []
    if username:
        jobs.append((
            "Perfil",
            "USER",
            f"https://www.tiktok.com/@{username.lstrip('@')}",
        ))
    if hashtag:
        tag = hashtag.lstrip("#")
        jobs.append((
            f"#{tag}",
            "HASHTAG",
            f"https://www.tiktok.com/tag/{tag}",
        ))

    for source, scrape_type, target_url in jobs:
        payload = {
            "type": scrape_type,
            "region": "BR",
            "url": target_url,
            "maxItems": int(max_items),
            "isUnlimited": False,
        }

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=300,
            )

            if not response.ok:
                detail = response.text[:500]
                errors.append(
                    f"{source}: Apify HTTP {response.status_code}: {detail}"
                )
                continue

            data = response.json()
            if not isinstance(data, list):
                errors.append(
                    f"{source}: resposta inesperada da Apify; "
                    "confira a saída do Actor."
                )
                continue

            for video in data:
                item = normalize_apify_video(video, source)
                if item:
                    results.append(item)

        except requests.RequestException as exc:
            errors.append(f"{source}: falha de conexão: {exc}")
        except ValueError:
            errors.append(f"{source}: a Apify não retornou JSON válido.")

    return results, errors


def run_collection(username, hashtag, max_items, ms_token=""):
    return collect_tiktok(username, hashtag, max_items, ms_token)
