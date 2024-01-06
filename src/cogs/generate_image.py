import logging
import time

import coloredlogs
import discord
import webuiapi
from discord import Color, Interaction
from discord import app_commands as ac
from discord.ext.commands import Bot

from utils import stable_diffusion as sd

PORT = 7861
coloredlogs.install()
logger = logging.getLogger(__name__)

_api = webuiapi.WebUIApi(port=PORT)
logger.info("Initialized sd-api")
_sd_models = sd.ModelsAPI(_api)
logger.debug("Initialized sd.ModelsAPI")
_sd_models.set_current_options(sd.Defaults.to_options())
logger.info("Applied sd-options")


class AutoCompletions:
    """モデル類のオートコンプリート系

    Returns:
        List[app_commands.Choice]: 候補のリスト
    """

    @classmethod
    async def model(cls, ctx: Interaction, inputted: str) -> list[ac.Choice]:
        models = _sd_models.get_models()
        if isinstance(ctx.channel, discord.TextChannel) and ctx.channel.is_nsfw():
            return await cls._candidate(inputted, models)
        else:
            models = [i for i in models if "nsfw" not in i]
            return await cls._candidate(inputted, models)

    @classmethod
    async def vae(cls, ctx: Interaction, inputted: str) -> list[ac.Choice]:
        vaes = _sd_models.get_vaes()
        return await cls._candidate(inputted, vaes)

    @classmethod
    async def sampler(cls, ctx: Interaction, inputted: str) -> list[ac.Choice]:
        samplers = [i.value for i in sd.Samplers]
        return await cls._candidate(inputted, samplers)

    @staticmethod
    async def _candidate(text: str, candidates: list) -> list[ac.Choice]:
        if text == "":
            return [ac.Choice(name=i, value=i) for i in candidates]
        return [ac.Choice(name=i, value=i) for i in candidates if text.lower() in i.lower()]


class SDCog(ac.Group):
    """Stable DiffusionのCog

    Args:
        bot (discord.ext.commands.Bot): Bot instance
    """

    def __init__(self, bot: Bot, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bot = bot

    @ac.command(name="txt2img")
    @ac.autocomplete(
        model=AutoCompletions.model,
        vae=AutoCompletions.vae,
        sampler=AutoCompletions.sampler,
    )
    async def generate(
        self,
        ctx: Interaction,
        prompt: str,
        negative_prompt: str = "",
        model: str = sd.Defaults.MODEL,
        vae: str = sd.Defaults.VAE_FULLNAME,
        sampler: str | None = None,
        height: int = 512,
        width: int = 512,
        steps: int = 20,
        seed: int = -1,
        cfg_scale: float = 7.0,
        ignore_default_negative_prompts: bool = False,
    ):
        option = sd.Options(model, vae)
        embed = None
        try:
            _sd_models.validate_options(option)
        except sd.ModelNotFound:
            embed = discord.Embed(title="エラー！", description="モデルがありません", color=Color.red())
        except sd.VAENotFound:
            embed = discord.Embed(title="エラー！", description="VAEがありません", color=Color.red())

        if embed:
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(title="生成中...", description="", color=Color.blue())
        await ctx.response.send_message(embed=embed)

        _sd_models.set_current_options(option)

        if sampler is None:
            sampler = sd.Defaults.SAMPLER  # dpm++ 2m karras
        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "sampler_name": sampler,
            "sampler_index": sampler,
            "height": height,
            "width": width,
            "steps": steps,
            "seed": seed,
            "cfg_scale": cfg_scale,
            "use_async": True,
        }
        # ネガティブプロンプトを調整
        negative_prompt = sd.format_negative_prompt(
            negative_prompt,
            isinstance(ctx.channel, discord.TextChannel) and (not ctx.channel.is_nsfw()),
            ignore_default_negative_prompts,
        )

        s_time = time.perf_counter()
        img = await _api.txt2img(**params)  # type: ignore
        p_time = time.perf_counter() - s_time

        result = discord.Embed(title=f"生成完了（{round(p_time, 2)}秒）", color=Color.blue())
        result.add_field(name="プロンプト", value=prompt[:1024])
        result.add_field(name="ネガティブプロンプト", value=negative_prompt[:1024])
        result.add_field(name="Seed", value=str(img.info["seed"]), inline=False)
        result.add_field(name="モデル", value=img.info["sd_model_name"], inline=False)
        attach = sd.image_to_discord_file(img.image)
        result.set_image(url=f"attachment://{attach.filename}")
        await ctx.edit_original_response(embed=result, attachments=[attach])

    @ac.command(name="txt2img-hires-fix", description="Hires.Fixで生成します")
    @ac.autocomplete(
        model=AutoCompletions.model,
        vae=AutoCompletions.vae,
        sampler=AutoCompletions.sampler,
    )
    async def hires_txt2img(
        self,
        ctx: Interaction,
        prompt: str,
        negative_prompt: str = "",
        model: str = sd.Defaults.MODEL,
        vae: str = sd.Defaults.VAE_FULLNAME,
        sampler: str | None = None,
        height: int = 512,
        width: int = 512,
        steps: int = 20,
        seed: int = -1,
        cfg_scale: float = 7.0,
        ignore_default_negative_prompts: bool = False,
    ):
        pass


async def setup(bot: Bot):
    bot.tree.add_command(SDCog(bot, name="sd"))
    print("Stable Diffusion cog added")
