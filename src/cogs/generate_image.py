import uuid
from io import BytesIO

import webuiapi
import discord
from discord import app_commands as ac
from discord.ext.commands import Bot

from utils import stable_diffusion as sd


PORT = 7861


class SDCog(ac.Group):
    """Stable DiffusionのCog

    Args:
        bot (discord.ext.commands.Bot): Bot instance
    """

    def __init__(self, bot: Bot, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bot = bot
        self.api = webuiapi.WebUIApi(port=PORT, sampler=sd.Samplers.DPM_2M_KARRAS)

    @ac.command(name="txt2img")
    async def generate(
        self,
        interaction: discord.Interaction,
        prompt: str,
        negative_prompt: str = "",
        height: int = 512,
        width: int = 512,
        steps: int = 20,
        seed: int = -1,
        cfg_scale: float = 7.0,
    ):
        a = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "height": height,
            "width": width,
            "steps": steps,
            "seed": seed,
            "cfg_scale": cfg_scale,
            "use_async": True,
        }
        embed = discord.Embed(title="生成中...", description="")
        await interaction.response.send_message(embed=embed)
        img = await self.api.txt2img(**a)  # type: ignore

        img_bytes = BytesIO()
        img.image.save(img_bytes, format="png")
        img_bytes.seek(0)  # ここ重要
        img_filename = str(uuid.uuid4()).replace("-", "") + ".png"
        print(img_filename)

        result = discord.Embed(title="生成完了")
        attach = discord.File(img_bytes, filename=img_filename)
        result.set_image(url=f"attachment://{img_filename}")
        await interaction.edit_original_response(embed=result, attachments=[attach])


async def setup(bot: Bot):
    bot.tree.add_command(SDCog(bot, name="sd"))
    print("Stable Diffusion cog added")
