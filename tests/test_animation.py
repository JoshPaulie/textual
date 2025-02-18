from time import perf_counter

from textual.app import App, ComposeResult
from textual.widgets import Static


class AnimApp(App):
    CSS = """
    #foo {
        height: 1;
    }

    """

    def compose(self) -> ComposeResult:
        yield Static("foo", id="foo")


async def test_animate_height() -> None:
    """Test animating styles.height works."""

    # Styles.height is a scalar, which makes it more complicated to animate

    app = AnimApp()

    async with app.run_test() as pilot:
        static = app.query_one(Static)
        assert static.size.height == 1
        assert static.styles.height.value == 1
        static.styles.animate("height", 100, duration=0.5, easing="linear")
        start = perf_counter()

        # Wait for the animation to finished
        await pilot.wait_for_animation()
        elapsed = perf_counter() - start
        # Check that the full time has elapsed
        assert elapsed >= 0.5
        # Check the height reached the maximum
        assert static.styles.height.value == 100


async def test_scheduling_animation() -> None:
    """Test that scheduling an animation works."""

    app = AnimApp()
    delay = 0.1

    async with app.run_test() as pilot:
        styles = app.query_one(Static).styles
        styles.background = "black"

        styles.animate("background", "white", delay=delay, duration=0)

        await pilot.pause(0.9 * delay)
        assert styles.background.rgb == (0, 0, 0)  # Still black

        await pilot.wait_for_scheduled_animations()
        assert styles.background.rgb == (255, 255, 255)


async def test_wait_for_current_animations() -> None:
    """Test that we can wait only for the current animations taking place."""

    app = AnimApp()

    delay = 10

    async with app.run_test() as pilot:
        styles = app.query_one(Static).styles
        styles.animate("height", 100, duration=0.1)
        start = perf_counter()
        styles.animate("height", 200, duration=0.1, delay=delay)

        # Wait for the first animation to finish
        await pilot.wait_for_animation()
        elapsed = perf_counter() - start
        assert elapsed < (delay / 2)


async def test_wait_for_current_and_scheduled_animations() -> None:
    """Test that we can wait for current and scheduled animations."""

    app = AnimApp()

    async with app.run_test() as pilot:
        styles = app.query_one(Static).styles

        start = perf_counter()
        styles.animate("height", 50, duration=0.01)
        styles.animate("background", "black", duration=0.01, delay=0.05)

        await pilot.wait_for_scheduled_animations()
        elapsed = perf_counter() - start
        assert elapsed >= 0.06
        assert styles.background.rgb == (0, 0, 0)


async def test_reverse_animations() -> None:
    """Test that you can create reverse animations.

    Regression test for #1372 https://github.com/Textualize/textual/issues/1372
    """

    app = AnimApp()

    async with app.run_test() as pilot:
        static = app.query_one(Static)
        styles = static.styles

        # Starting point.
        styles.background = "black"
        assert styles.background.rgb == (0, 0, 0)

        # First, make sure we can go from black to white and back, step by step.
        styles.animate("background", "white", duration=0.01)
        await pilot.wait_for_animation()
        assert styles.background.rgb == (255, 255, 255)

        styles.animate("background", "black", duration=0.01)
        await pilot.wait_for_animation()
        assert styles.background.rgb == (0, 0, 0)

        # Now, the actual test is to make sure we go back to black if creating both at once.
        styles.animate("background", "white", duration=0.01)
        styles.animate("background", "black", duration=0.01)
        await pilot.wait_for_animation()
        assert styles.background.rgb == (0, 0, 0)


async def test_schedule_reverse_animations() -> None:
    """Test that you can schedule reverse animations.

    Regression test for #1372 https://github.com/Textualize/textual/issues/1372
    """

    app = AnimApp()

    async with app.run_test() as pilot:
        static = app.query_one(Static)
        styles = static.styles

        # Starting point.
        styles.background = "black"
        assert styles.background.rgb == (0, 0, 0)

        # First, make sure we can go from black to white and back, step by step.
        styles.animate("background", "white", delay=0.01, duration=0.01)
        await pilot.wait_for_scheduled_animations()
        assert styles.background.rgb == (255, 255, 255)

        styles.animate("background", "black", delay=0.01, duration=0.01)
        await pilot.wait_for_scheduled_animations()
        assert styles.background.rgb == (0, 0, 0)

        # Now, the actual test is to make sure we go back to black if scheduling both at once.
        styles.animate("background", "white", delay=0.01, duration=0.01)
        await pilot.pause(0.005)
        styles.animate("background", "black", delay=0.01, duration=0.01)
        await pilot.wait_for_scheduled_animations()
        assert styles.background.rgb == (0, 0, 0)
