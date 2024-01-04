import uuid
import logging
from io import BytesIO

import coloredlogs
import webuiapi
import discord
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
    @classmethod
    async def model(cls, ctx: discord.Interaction, inputted: str):
        models = _sd_models.get_models()
        return await cls._candidate(inputted, models)

    @classmethod
    async def vae(cls, ctx: discord.Interaction, inputted: str):
        vaes = _sd_models.get_vaes()
        return await cls._candidate(inputted, vaes)

    @classmethod
    async def sampler(cls, ctx: discord.Interaction, inputted: str):
        samplers = [i.value for i in sd.Samplers]
        return await cls._candidate(inputted, samplers)

    @staticmethod
    async def _candidate(text: str, candidates: list):
        if text == "":
            return [ac.Choice(name=i, value=i) for i in candidates]
        return [ac.Choice(name=i, value=i) for i in candidates if text.lower() in i.lower()]


class SDCog(ac.Group):
    """Stable DiffusionのCog

    Args:
        bot (discord.ext.commands.Bot): Bot instance
    """
    DEFAULT_OPTIONS = {
        "sd_model_checkpoint": "Anything-v4.5-pruned-mergedVae"
    }

    def __init__(self, bot: Bot, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bot = bot

    @ac.command(name="txt2img")
    @ac.autocomplete(
        model=AutoCompletions.model,
        vae=AutoCompletions.vae,
        sampler=AutoCompletions.sampler
    )
    async def generate(
        self,
        interaction: discord.Interaction,
        prompt: str,
        negative_prompt: str = "",
        model: str | None = None,
        vae: str | None = None,
        sampler: str | None = None,
        height: int = 512,
        width: int = 512,
        steps: int = 20,
        seed: int = -1,
        cfg_scale: float = 7.0,
        ignore_easynegative: bool = False
    ):

        option = sd.Defaults.to_options()

        embed = None
        if model and model not in _sd_models.get_models():
            embed = discord.Embed(title="エラー！", description="モデルがありません", color=discord.Color.red())
        elif vae and vae not in _sd_models.get_vaes():
            embed = discord.Embed(title="エラー！", description="VAEがありません", color=discord.Color.red())
        elif model:
            option.model = model
        elif vae:
            option.vae = vae

        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(title="生成中...", description="", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

        _sd_models.set_current_options(option)

        if sampler is None:
            sampler = sd.Defaults.SAMPLER  # dpm++ 2m karras
        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "sampler_name": sampler,
            "height": height,
            "width": width,
            "steps": steps,
            "seed": seed,
            "cfg_scale": cfg_scale,
            "use_async": True,
        }
        _negative = map(lambda x: x.replace(" ", ""), params["negative_prompt"].split(","))
        if sd.Defaults.EMBEDDING not in _negative and not ignore_easynegative:
            params["negative_prompt"] = sd.Defaults.EMBEDDING + "," + params["negative_prompt"]

        img = await _api.txt2img(**params)  # type: ignore

        img_bytes = BytesIO()
        img.image.save(img_bytes, format="png")
        img_bytes.seek(0)  # ここ重要
        img_filename = str(uuid.uuid4()).replace("-", "") + ".png"

        result = discord.Embed(title="生成完了", color=discord.Color.blue())
        attach = discord.File(img_bytes, filename=img_filename)
        result.set_image(url=f"attachment://{img_filename}")
        await interaction.edit_original_response(embed=result, attachments=[attach])


async def setup(bot: Bot):
    bot.tree.add_command(SDCog(bot, name="sd"))
    print("Stable Diffusion cog added")
