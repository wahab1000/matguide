"""
Seed starter data into the database.

This inserts the MatGuide technique library when the project is first run.
Each technique includes a YouTube link to an original instructional video.
"""

from models import Technique
from extensions import db


def seed_techniques():
    """
    Add starter technique data only if the table is empty.
    """
    if Technique.query.first():
        return

    starter_techniques = [
        Technique(
            name="Shrimp (Hip Escape)",
            category="Escapes",
            level="Beginner",
            description=(
                "A fundamental movement used to create space, recover guard, and escape pressure. "
                "Important details include framing correctly, moving the hips away, and keeping distance."
            ),
            youtube_url="https://youtu.be/d2e2XVtyjwo"
        ),
        Technique(
            name="Scissor Sweep",
            category="Sweeps",
            level="Beginner",
            description=(
                "A basic sweep from guard that uses off-balancing, angle creation, and leg positioning "
                "to reverse the opponent and come on top."
            ),
            youtube_url="https://youtu.be/_1SPyonsIoE"
        ),
        Technique(
            name="Rolling Armbar",
            category="Submissions",
            level="Advanced",
            description=(
                "A dynamic armbar variation that uses rotational movement and timing to attack the arm. "
                "This technique requires control, balance, and awareness of momentum."
            ),
            youtube_url="https://youtu.be/0XhA3SGilpw"
        ),
        Technique(
            name="Knee Slide Guard Pass",
            category="Guard Passes",
            level="Intermediate",
            description=(
                "A pressure-based guard pass that uses upper-body control and knee positioning to pass "
                "through the opponent’s legs while maintaining balance and pressure."
            ),
            youtube_url="https://youtu.be/RKSb4pyp5oA"
        ),
        Technique(
            name="Hip Throw",
            category="Takedowns",
            level="Intermediate",
            description=(
                "A takedown that uses hip positioning, balance disruption, and upper-body control to lift "
                "and throw the opponent. Timing and body placement are key."
            ),
            youtube_url="https://youtu.be/86jSw0s1hVE"
        ),
        Technique(
            name="Hip Bump Sweep",
            category="Sweeps",
            level="Beginner",
            description=(
                "A simple sweep that uses posture breaking, sitting up, and hip movement to knock the "
                "opponent backwards and reverse the position."
            ),
            youtube_url="https://youtu.be/CwMbcRubO8c"
        ),
        Technique(
            name="Double Leg Takedown",
            category="Takedowns",
            level="Beginner",
            description=(
                "A fundamental takedown that attacks both legs at once. Important points include level "
                "change, penetration step, driving through, and finishing with control."
            ),
            youtube_url="https://youtu.be/g-1CxfXPrF4"
        ),
        Technique(
            name="Cross Collar Choke",
            category="Submissions",
            level="Intermediate",
            description=(
                "A collar-based choke that relies on deep grips, forearm pressure, and proper elbow "
                "positioning to create an effective submission using the gi."
            ),
            youtube_url="https://youtu.be/QdE2yKvSlfk"
        ),
        Technique(
            name="Bridge and Roll Escape",
            category="Escapes",
            level="Beginner",
            description=(
                "A fundamental escape that uses bridging power, trapping, and rotational movement to reverse "
                "a top position and recover from pressure."
            ),
            youtube_url="https://youtu.be/_pPAghyMf9M"
        ),
        Technique(
            name="Berimbolo",
            category="Advanced Transitions",
            level="Advanced",
            description=(
                "A modern inversion-based technique used to expose the back or create a dominant angle. "
                "It requires timing, mobility, and familiarity with rotational control."
            ),
            youtube_url="https://youtu.be/AImhfluWRVU"
        ),
    ]

    db.session.add_all(starter_techniques)
    db.session.commit()