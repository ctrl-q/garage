#!/usr/bin/env python3
"""
This is an example to train a task with PPO algorithm.

Here it creates InvertedDoublePendulum using gym. And uses a PPO with 1M
steps.

Results:
    AverageDiscountedReturn: 500
    RiseTime: itr 40

"""
import random

import tensorflow as tf
from garage.envs import normalize, GarageEnv
from garage.envs.ml1_wrapper import ML1WithPinnedGoal
from garage.envs.multi_env_wrapper import MultiEnvWrapper, round_robin_strategy
from garage.envs.multi_task_metaworld_wrapper import MTMetaWorldWrapper
from garage.experiment.deterministic import set_seed
from garage.tf.algos import PPO
from garage.tf.baselines import GaussianMLPBaseline
from garage.tf.envs import TfEnv
from garage.tf.experiment import LocalTFRunner
from garage.tf.policies import GaussianMLPPolicy
from metaworld.envs.mujoco.env_dict import EASY_MODE_ARGS_KWARGS
from metaworld.envs.mujoco.env_dict import EASY_MODE_CLS_DICT
from garage import wrap_experiment


@wrap_experiment
def ppo_ml1_reach(ctxt=None, seed=1):

    env_id = "reach-v1"

    """Run task."""
    set_seed(seed)
    with LocalTFRunner(snapshot_config=ctxt) as runner:
        Ml1_reach_envs = get_ML1_envs_test(env_id)
        env = MTMetaWorldWrapper(Ml1_reach_envs, [env_id] * len(Ml1_reach_envs))

        policy = GaussianMLPPolicy(
            env_spec=env.spec,
            hidden_sizes=(64, 64),
            hidden_nonlinearity=tf.nn.relu,
            output_nonlinearity=None,
        )

        baseline = GaussianMLPBaseline(
            env_spec=env.spec,
            regressor_args=dict(
                hidden_sizes=(64, 64),
                use_trust_region=True,
            ),
        )

        algo = PPO(
            env_spec=env.spec,
            policy=policy,
            baseline=baseline,
            max_path_length=150,
            discount=0.99,
            gae_lambda=0.95,
            lr_clip_range=0.2,
            optimizer_args=dict(
                batch_size=32,
                max_epochs=10,
                tf_optimizer_args=dict(
                    learning_rate=3e-4,
                ),
            ),
            stop_entropy_gradient=True,
            entropy_method='max',
            policy_ent_coeff=0.002,
            center_adv=False,
        )

        runner.setup(algo, env)
        runner.train(n_epochs=99999, batch_size=4096, plot=False)


def get_ML1_envs_test(name):
    bench = ML1WithPinnedGoal.get_train_tasks(name)
    tasks = [{'task': 0, 'goal': i} for i in range(50)]
    ret = {}
    for task in tasks:
        new_bench = bench.clone(bench)
        new_bench.set_task(task)
        ret[("goal"+str(task['goal']))] = GarageEnv((new_bench.active_env))
    return ret


seeds = random.sample(range(100), 1)
for seed in seeds:
    ppo_ml1_reach(seed=seed)