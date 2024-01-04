import webuiapi
from dataclasses import dataclass
from discord import app_commands as ac
from enum import Enum


# stable-diffusion-webui V1.7.0のサンプラー
class Samplers(Enum):
    DPM_2M_KARRAS = "DPM++ 2M Karras"
    DPM_SDE_KARRAS = "DPM++ SDE Karras"
    DPM_2M_SDE_EXPONENTIAL = "DPM++ 2M SDE Exponential"
    DPM_2M_SDE_KARRAS = "DPM++ 2M SDE Karras"
    EULER_A = "Euler a"
    EULER = "Euler"
    LMS = "LMS"
    HEUN = "Heun"
    DPM2 = "DPM2"
    DPM2_A = "DPM2 a"
    DPM_2S_A = "DPM++ 2S a"
    DPM_2M = "DPM++ 2M"
    DPM_SDE = "DPM++ SDE"
    DPM_2M_SDE = "DPM++ 2M SDE"
    DPM_2M_SDE_HEUN = "DPM++ 2M SDE Heun"
    DPM_2M_SDE_HEUN_KARRAS = "DPM++ 2M SDE Heun Karras"
    DPM_2M_SDE_HEUN_EXPONENTIAL = "DPM++ 2M SDE Heun Exponential"
    DPM_3M_SDE = "DPM++ 3M SDE"
    DPM_3M_SDE_KARRAS = "DPM++ 3M SDE Karras"
    DPM_3M_SDE_EXPONENTIAL = "DPM++ 3M SDE Exponential"
    DPM_FAST = "DPM fast"
    DPM_ADAPTIVE = "DPM adaptive"
    LMS_KARRAS = "LMS Karras"
    DPM2_KARRAS = "DPM2 Karras"
    DPM2_A_KARRAS = "DPM2 a Karras"
    DPM_2S_A_KARRAS = "DPM++ 2S a Karras"
    RESTART = "Restart"
    DDIM = "DDIM"
    PLMS = "PLMS"
    UNIPC = "UniPC"


@dataclass
class Options:
    model: str
    vae: str


class Defaults:
    MODEL = "Anything-v4.5-pruned-mergedVae"
    VAE = "clearvae_v23"
    VAE_FULLNAME = "clearvae_v23.safetensors"
    EMBEDDING = "EasyNegative"
    SAMPLER = Samplers.DPM_2M_KARRAS.value

    @classmethod
    def to_dict(cls):
        return {
            "sd_model_checkpoint": cls.MODEL,
            "sd_vae": cls.VAE
        }

    @classmethod
    def to_options(cls):
        return Options(
            model=cls.MODEL,
            vae=cls.VAE
        )


class ModelsAPI:
    def __init__(self, api: webuiapi.WebUIApi) -> None:
        self.api = api

    def get_current_options(self):
        options = self.api.get_options()
        return Options(
            model=options["sd_model_checkpoint"],
            vae=options["sd_vae"]
        )

    def set_current_options(self, options: Options):
        self.api.set_options({"sd_model_checkpoint": options.model, "sd_vae": options.vae})

    def get_models(self):
        return [i["model_name"] for i in self.api.get_sd_models()]

    def get_vaes(self):
        return [i["model_name"].removesuffix(".safetensors").removesuffix(".vae.pt") for i in self.api.get_sd_vae()]

    def get_embeddings(self):
        return list(self.api.get_embeddings()["loaded"].keys())


def _format_name(name: str, upper: bool = True) -> str:
    if upper:
        name = name.upper()
    return name.replace("", "_").replace("-", "_").replace("+", "")


def make_choices(choices: list):
    return [ac.Choice(name=i, value=i) for i in choices]
