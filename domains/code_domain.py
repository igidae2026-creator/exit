import random


def generate():
    return {
        "quality": random.random(),
        "novelty": random.random(),
        "diversity": random.random(),
        "efficiency": random.random(),
        "cost": random.random(),
    }
