import numpy as np
from faker import Faker
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.provider import Provider
from app.db.models.provider_state import ProviderStateHistory

SERVICE_TYPES = ["plumbing", "electrical", "appliance_repair", "cleaning", "pest_control", "locksmith"]
REGIONS = [
    ("colombo-01", 6.9344, 79.8428),
    ("colombo-02", 6.9271, 79.8612),
    ("dehiwala", 6.8500, 79.8667),
    ("mount-lavinia", 6.8389, 79.8653),
    ("kotte", 6.8905, 79.9021),
]

# Faker has no si_LK locale, so provider names are drawn from a curated list of common
# Sinhalese given names and surnames -- the seeded city is Colombo, so English/Western
# Faker names read wrong for this demo.
MALE_FIRST_NAMES = [
    "Nimal", "Sunil", "Kamal", "Chaminda", "Priyantha", "Kumara", "Ranjith", "Saman",
    "Ajith", "Nuwan", "Dilshan", "Chathura", "Tharindu", "Lasantha", "Malith", "Roshan",
    "Anura", "Gayan", "Chandana", "Prasad", "Ruwan", "Janaka", "Susantha", "Wasantha",
    "Amila", "Buddhika", "Indika", "Rohana", "Sanjeewa", "Upul",
]
FEMALE_FIRST_NAMES = [
    "Nirosha", "Chamari", "Anusha", "Kumari", "Priyanka", "Dilrukshi", "Malini", "Sanduni",
    "Iresha", "Hasini", "Chathurika", "Nadeeka", "Wasana", "Erandi", "Manori", "Kavindi",
    "Thilini", "Sachini", "Dilani", "Ishara", "Nayomi", "Rasika", "Shanika", "Vindya",
    "Kanchana", "Menaka", "Piyumi", "Ramani", "Sulochana", "Tharushi",
]
SURNAMES = [
    "Jayasinghe", "Perera", "Fernando", "Silva", "Wickramasinghe", "Rajapaksha",
    "Gunasekara", "Bandara", "Dissanayake", "Karunaratne", "Weerasinghe", "Kodikara",
    "Senanayake", "Amarasinghe", "Ekanayake", "Herath", "Mendis", "Wijesinghe",
    "Ranasinghe", "Gunawardena", "Jayawardena", "Abeysekara", "Rathnayake", "Wijeratne",
    "Dias", "Peiris", "Fonseka", "Samarasinghe", "Kularatne", "Munasinghe",
]

# Verified live (HTTP 200) against images.unsplash.com before use -- see PR discussion.
AVATAR_URLS = [
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1544723795-3fb6469f5b39?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1552058544-f2b08422138a?auto=format&fit=crop&w=200&h=200&q=80",
    "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=200&h=200&q=80",
]


async def seed_providers(session: AsyncSession, n: int = 150, seed: int = 42) -> list[Provider]:
    """Clears any existing providers (and their state history) before seeding fresh --
    running this script more than once must never accumulate duplicate rows."""
    await session.execute(delete(ProviderStateHistory))
    await session.execute(delete(Provider))
    await session.commit()

    rng = np.random.default_rng(seed)
    faker = Faker()
    Faker.seed(seed)

    providers: list[Provider] = []
    for _ in range(n):
        service_type = SERVICE_TYPES[rng.integers(0, len(SERVICE_TYPES))]
        region_name, base_lat, base_lon = REGIONS[rng.integers(0, len(REGIONS))]
        lat = base_lat + rng.normal(0, 0.01)
        lon = base_lon + rng.normal(0, 0.01)
        rating = float(np.clip(rng.normal(4.0, 0.6), 1.0, 5.0))
        response_speed = float(np.clip(rng.normal(20.0, 8.0), 5.0, 60.0))
        years_experience = int(np.clip(rng.integers(1, 26), 1, 25))

        first_names = MALE_FIRST_NAMES if rng.integers(0, 2) == 0 else FEMALE_FIRST_NAMES
        name = f"{first_names[rng.integers(0, len(first_names))]} {SURNAMES[rng.integers(0, len(SURNAMES))]}"
        phone = f"+94 7{rng.integers(0, 10)} {rng.integers(100, 1000)} {rng.integers(1000, 10000)}"
        avatar_url = AVATAR_URLS[rng.integers(0, len(AVATAR_URLS))]

        provider = Provider(
            name=name,
            service_type=service_type,
            region=region_name,
            lat=lat,
            lon=lon,
            rating=round(rating, 2),
            base_response_speed=round(response_speed, 1),
            phone=phone,
            years_experience=years_experience,
            avatar_url=avatar_url,
            profile_text=(
                f"{service_type.replace('_', ' ').title()} service operating in "
                f"{region_name.replace('-', ' ').title()}, {years_experience} years experience. "
                f"{faker.sentence(nb_words=12)}"
            ),
        )
        providers.append(provider)

    session.add_all(providers)
    await session.commit()
    return providers


async def _main() -> None:
    from app.core.config import get_settings
    from app.db.session import get_session

    settings = get_settings()
    async with get_session() as session:
        created = await seed_providers(session, n=150, seed=settings.seed)
        print(f"Seeded {len(created)} providers with seed={settings.seed}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
