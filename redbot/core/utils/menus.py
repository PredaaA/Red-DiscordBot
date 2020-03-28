# Original source of reaction-based menu idea from
# https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py
#
# Ported to Red V3 by Palm\_\_ (https://github.com/palmtree5)
import asyncio
import contextlib
import functools
import warnings
from typing import Union, Iterable, List, Optional, Union, Mapping
import discord

from .. import commands
from .predicates import ReactionPredicate

_ReactableEmoji = Union[str, discord.Emoji]

PREFERED_CONTROLS = {}


def update_controls(bot):  # Call this at the init to update the globals
    global PREFERED_CONTROLS

    PREFERED_CONTROLS.update(
        {
            "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}": bot.get_emoji(
                647175085592936458
            )
        }
    )
    PREFERED_CONTROLS.update({"\N{LEFTWARDS BLACK ARROW}": bot.get_emoji(647175085592936458)})
    PREFERED_CONTROLS.update({"⬅️": bot.get_emoji(647175085592936458)})
    PREFERED_CONTROLS.update({"⬅": bot.get_emoji(647175085592936458)})

    PREFERED_CONTROLS.update({"\N{CROSS MARK}": bot.get_emoji(632685164408995870)})
    PREFERED_CONTROLS.update({"❌": bot.get_emoji(632685164408995870)})

    PREFERED_CONTROLS.update(
        {
            "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}": bot.get_emoji(
                647178261394358325
            )
        }
    )
    PREFERED_CONTROLS.update({"\N{BLACK RIGHTWARDS ARROW}": bot.get_emoji(647178261394358325)})
    PREFERED_CONTROLS.update({"➡️": bot.get_emoji(647178261394358325)})
    PREFERED_CONTROLS.update({"➡": bot.get_emoji(647178261394358325)})


def update_icons(ctx: commands.Context, controls: Mapping, prefered_controls: Mapping) -> Mapping:
    has_external_emoji = ctx.me.permissions_in(ctx.channel).external_emojis
    if not has_external_emoji:
        return controls
    items = controls.items()
    new_controls = {}
    for i, v in items:
        new_emoji = prefered_controls.get(i) or i
        new_controls.update({new_emoji: v})
    return new_controls


def update_icon_adding(message: discord.Message, emojis: Iterable[_ReactableEmoji]):
    channel = message.channel
    guild = getattr(channel, "guild", None)
    if guild:
        user = guild.me
    else:
        user = channel.me
    has_external_emoji = message.channel.permissions_for(user).external_emojis

    if not has_external_emoji:
        return emojis
    newemojis = []
    for i in emojis:
        newemojis.append(PREFERED_CONTROLS.get(i) or i)
    return newemojis


async def menu(
    ctx: commands.Context,
    pages: Union[List[str], List[discord.Embed]],
    controls: dict,
    message: discord.Message = None,
    page: int = 0,
    timeout: float = 30.0,
):
    """
    An emoji-based menu

    .. note:: All pages should be of the same type

    .. note:: All functions for handling what a particular emoji does
              should be coroutines (i.e. :code:`async def`). Additionally,
              they must take all of the parameters of this function, in
              addition to a string representing the emoji reacted with.
              This parameter should be the last one, and none of the
              parameters in the handling functions are optional

    Parameters
    ----------
    ctx: commands.Context
        The command context
    pages: `list` of `str` or `discord.Embed`
        The pages of the menu.
    controls: dict
        A mapping of emoji to the function which handles the action for the
        emoji.
    message: discord.Message
        The message representing the menu. Usually :code:`None` when first opening
        the menu
    page: int
        The current page number of the menu
    timeout: float
        The time (in seconds) to wait for a reaction

    Raises
    ------
    RuntimeError
        If either of the notes above are violated
    """
    if not isinstance(pages[0], (discord.Embed, str)):
        raise RuntimeError("Pages must be of type discord.Embed or str")
    if not all(isinstance(x, discord.Embed) for x in pages) and not all(
        isinstance(x, str) for x in pages
    ):
        raise RuntimeError("All pages must be of the same type")
    new_controls = update_icons(ctx, controls, PREFERED_CONTROLS)
    for key, value in new_controls.items():
        maybe_coro = value
        if isinstance(value, functools.partial):
            maybe_coro = value.func
        if not asyncio.iscoroutinefunction(maybe_coro):
            raise RuntimeError("Function must be a coroutine")
    current_page = pages[page]

    if not message:
        if isinstance(current_page, discord.Embed):
            message = await ctx.send(embed=current_page)
        else:
            message = await ctx.send(current_page)
        # Don't wait for reactions to be added (GH-1797)
        # noinspection PyAsyncCall
<<<<<<< HEAD
        start_adding_reactions(message, new_controls.keys(), ctx.bot.loop)
=======
        start_adding_reactions(message, controls.keys())
>>>>>>> eebea59... Remove usage of `loop` arg in calls to `start_adding_reactions` (#3644)
    else:
        try:
            if isinstance(current_page, discord.Embed):
                await message.edit(embed=current_page)
            else:
                await message.edit(content=current_page)
        except discord.NotFound:
            return

    try:
        react, user = await ctx.bot.wait_for(
            "reaction_add",
            check=ReactionPredicate.with_emojis(tuple(new_controls.keys()), message, ctx.author),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        try:
            if message.channel.permissions_for(ctx.me).manage_messages:
                await message.clear_reactions()
            else:
                raise RuntimeError
        except (discord.Forbidden, RuntimeError):  # cannot remove all reactions
            for key in controls.keys():
                try:
                    await message.remove_reaction(key, ctx.bot.user)
                except discord.Forbidden:
                    return
                except discord.HTTPException:
                    pass
        except discord.NotFound:
            return
    else:
        return await new_controls[react.emoji](
            ctx, pages, new_controls, message, page, timeout, react.emoji
        )


async def next_page(
    ctx: commands.Context,
    pages: list,
    controls: dict,
    message: discord.Message,
    page: int,
    timeout: float,
    emoji: str,
):
    perms = message.channel.permissions_for(ctx.me)
    if perms.manage_messages:  # Can manage messages, so remove react
        with contextlib.suppress(discord.NotFound):
            await message.remove_reaction(emoji, ctx.author)
    if page == len(pages) - 1:
        page = 0  # Loop around to the first item
    else:
        page = page + 1
    return await menu(ctx, pages, controls, message=message, page=page, timeout=timeout)


async def prev_page(
    ctx: commands.Context,
    pages: list,
    controls: dict,
    message: discord.Message,
    page: int,
    timeout: float,
    emoji: str,
):
    perms = message.channel.permissions_for(ctx.me)
    if perms.manage_messages:  # Can manage messages, so remove react
        with contextlib.suppress(discord.NotFound):
            await message.remove_reaction(emoji, ctx.author)
    if page == 0:
        page = len(pages) - 1  # Loop around to the last item
    else:
        page = page - 1
    return await menu(ctx, pages, controls, message=message, page=page, timeout=timeout)


async def close_menu(
    ctx: commands.Context,
    pages: list,
    controls: dict,
    message: discord.Message,
    page: int,
    timeout: float,
    emoji: str,
):
    with contextlib.suppress(discord.NotFound):
        await message.delete()


def start_adding_reactions(
    message: discord.Message,
    emojis: Iterable[_ReactableEmoji],
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> asyncio.Task:
    """Start adding reactions to a message.

    This is a non-blocking operation - calling this will schedule the
    reactions being added, but the calling code will continue to
    execute asynchronously. There is no need to await this function.

    This is particularly useful if you wish to start waiting for a
    reaction whilst the reactions are still being added - in fact,
    this is exactly what `menu` uses to do that.

    This spawns a `asyncio.Task` object and schedules it on ``loop``.
    If ``loop`` omitted, the loop will be retrieved with
    `asyncio.get_event_loop`.

    Parameters
    ----------
    message: discord.Message
        The message to add reactions to.
    emojis : Iterable[Union[str, discord.Emoji]]
        The emojis to react to the message with.
    loop : Optional[asyncio.AbstractEventLoop]
        The event loop.

    Returns
    -------
    asyncio.Task
        The task for the coroutine adding the reactions.

    """
    new_emojis = update_icon_adding(message, emojis)

    async def task():
        # The task should exit silently if the message is deleted
        with contextlib.suppress(discord.NotFound):
            for emoji in new_emojis:
                await message.add_reaction(emoji)

    if loop is None:
        loop = asyncio.get_running_loop()
    else:
        warnings.warn(
            "Explicitly passing the loop will not work in Red 3.4+",
            DeprecationWarning,
            stacklevel=2,
        )

    return loop.create_task(task())


DEFAULT_CONTROLS = {"⬅": prev_page, "❌": close_menu, "➡": next_page}
