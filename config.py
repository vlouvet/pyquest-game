# config.py
import os


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Difficulty knobs (override via env vars)
    DIFFICULTY_MULTIPLIER = float(os.environ.get('DIFFICULTY_MULTIPLIER', 1.0))
    MONSTER_HP_MIN = int(os.environ.get('MONSTER_HP_MIN', 60))
    MONSTER_HP_MAX = int(os.environ.get('MONSTER_HP_MAX', 120))
    COUNTER_ATTACK_CHANCE = int(os.environ.get('COUNTER_ATTACK_CHANCE', 70))
    COUNTER_DAMAGE_MIN = int(os.environ.get('COUNTER_DAMAGE_MIN', 5))
    COUNTER_DAMAGE_MAX = int(os.environ.get('COUNTER_DAMAGE_MAX', 15))
    HEALING_NERF_PERCENT = int(os.environ.get('HEALING_NERF_PERCENT', 20))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///pyquest.db'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DEBUG = False
    WTF_CSRF_ENABLED = False
    # Testing-friendly combat knobs to match assertions
    MONSTER_HP_MIN = 30
    MONSTER_HP_MAX = 70
    COUNTER_ATTACK_CHANCE = 50
    COUNTER_DAMAGE_MIN = 3
    COUNTER_DAMAGE_MAX = 10
    HEALING_NERF_PERCENT = 0


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///pyquest.db'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
