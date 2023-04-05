# Owner(s): ["module: dynamo"]
import functools
import unittest
from copy import deepcopy

import torch

import torch._dynamo
import torch._dynamo.backends.ipex
import torch._dynamo.test_case
from torch._dynamo.testing import same
from torch.testing._internal.inductor_utils import HAS_CUDA

requires_cuda = functools.partial(unittest.skipIf, not HAS_CUDA, "requires cuda")


class Seq(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(10, 10),
            torch.nn.ReLU(),
            torch.nn.Linear(10, 10),
            torch.nn.Sigmoid(),
        )

    def forward(self, x):
        return self.layers(x)


def init_weights(m):
    if isinstance(m, torch.nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight)
        m.bias.data.fill_(0.01)


class TestCompileTrainStep(torch._dynamo.test_case.TestCase):
    def test_no_optimizer(self):
        def train_step(model, inputs):
            out = model(*inputs)
            loss = out.sum()
            loss.backward()
            return loss

        model = Seq()
        model.apply(init_weights)
        inputs = [torch.randn((128, 10))]

        correct_loss = train_step(model, inputs)

        opt_train_step = torch.compile(train_step, backend="train_step_eager")
        opt_loss = opt_train_step(model, inputs)

        self.assertTrue(same(correct_loss, opt_loss))

    def test_sgd_optimizer(self):
        def train_step(model, optimizer, inputs):
            out = model(*inputs)
            loss = out.sum()
            loss.backward()
            optimizer.step()
            model.zero_grad()
            return loss

        model = Seq()
        model.apply(init_weights)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
        # copy the model/optimizer up front so we don't have to reset them between eager/compile runs
        opt_model = deepcopy(model)
        opt_optimizer = deepcopy(optimizer)
        inputs = [torch.randn((128, 10))]

        correct_loss = train_step(model, optimizer, inputs)
        correct_params = {
            name: param.clone().detach() for name, param in model.named_parameters()
        }

        opt_train_step = torch.compile(train_step, backend="train_step_eager")
        opt_loss = opt_train_step(opt_model, opt_optimizer, inputs)
        opt_params = {
            name: param.clone().detach() for name, param in opt_model.named_parameters()
        }

        for name in correct_params:
            self.assertTrue(name in opt_params)
            self.assertTrue(same(correct_params[name], opt_params[name]))
        self.assertTrue(same(correct_loss, opt_loss))


if __name__ == "__main__":
    from torch._dynamo.test_case import run_tests

    run_tests()
