import unittest

import numpy as np
import torch

from trojai.modelgen.default_optimizer import DefaultOptimizer, _eval_acc, _eval_binary_acc, train_val_dataset_split
from trojai.modelgen.config import DefaultOptimizerConfig, TrainingConfig

"""
Contains unittests related to 
"""
SEED = 1234


class TestRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.rso = np.random.RandomState(SEED)

    def tearDown(self):
        pass

    def test_accuracy(self):
        cfg = DefaultOptimizerConfig()
        optimizer_obj = DefaultOptimizer(cfg)
        batch_size = cfg.training_cfg.batch_size
        num_outputs = 5

        random_mat = self.rso.rand(batch_size, num_outputs)
        row_sum = random_mat.sum(axis=1)

        # normalize the random_mat such that every row adds up to 1
        # broadcast so we can divide every element in matrix by the row's sum
        fake_network_output = random_mat/row_sum[:,None]
        network_output = np.argmax(fake_network_output, axis=1)

        # now, modify a subset of the netowrk output and make that the "real" output
        true_output = network_output.copy()
        target_accuracy = 0.8
        num_indices_to_modify = int(batch_size*(1-target_accuracy))
        num_indices_unmodified = batch_size-num_indices_to_modify
        indices_to_modify = self.rso.choice(range(batch_size), num_indices_to_modify, replace=False)
        expected_accuracy = float(num_indices_unmodified)/float(batch_size) * 100

        for ii in indices_to_modify:
            true_output[ii] = true_output[ii]+1

        # convert datatypes to what is expected during operation
        network_output_pt = torch.tensor(fake_network_output, dtype=torch.float)
        true_output_pt = torch.tensor(true_output, dtype=torch.long)

        # now compute the accuracy
        actual_acc, n_total, n_correct = \
            _eval_acc(network_output_pt, true_output_pt, n_total=0, n_correct=0)
        self.assertAlmostEqual(actual_acc, expected_accuracy)

    def test_running_accuracy(self):
        batch_size = 32
        num_outputs = 5

        random_mat = self.rso.rand(batch_size, num_outputs)
        row_sum = random_mat.sum(axis=1)

        # normalize the random_mat such that every row adds up to 1
        # broadcast so we can divide every element in matrix by the row's sum
        fake_network_output = random_mat/row_sum[:, None]
        network_output = np.argmax(fake_network_output, axis=1)

        # now, modify a subset of the netowrk output and make that the "real" output
        true_output = network_output.copy()
        target_accuracy = 0.8
        num_indices_to_modify = int(batch_size*(1-target_accuracy))
        num_indices_unmodified = batch_size-num_indices_to_modify
        indices_to_modify = self.rso.choice(range(batch_size), num_indices_to_modify, replace=False)

        for ii in indices_to_modify:
            true_output[ii] = true_output[ii]+1

        # convert datatypes to what is expected during operation
        network_output_pt = torch.tensor(fake_network_output, dtype=torch.float)
        true_output_pt = torch.tensor(true_output, dtype=torch.long)

        # now compute the accuracy
        n_total_prev = 64
        n_correct_prev = 50
        expected_accuracy = (num_indices_unmodified+n_correct_prev)/(batch_size+n_total_prev) * 100
        expected_n_total = n_total_prev+batch_size
        expected_n_correct = n_correct_prev + num_indices_unmodified

        actual_acc, n_total, n_correct = \
            _eval_acc(network_output_pt, true_output_pt, n_total=n_total_prev, n_correct=n_correct_prev)
        self.assertAlmostEqual(actual_acc, expected_accuracy)
        self.assertEqual(expected_n_total, n_total)
        self.assertEqual(expected_n_correct, n_correct)

    def test_eval_binary_accuracy(self):
        batch_size = 32
        num_outputs = 2

        random_mat = self.rso.rand(batch_size, num_outputs)
        row_sum = random_mat.sum(axis=1)

        # normalize the random_mat such that every row adds up to 1
        # broadcast so we can divide every element in matrix by the row's sum
        fake_network_output = random_mat/row_sum[:, None]
        network_output = np.argmax(fake_network_output, axis=1)

        # now, modify a subset of the netowrk output and make that the "real" output
        true_output = network_output.copy()
        target_accuracy = 0.8
        num_indices_to_modify = int(batch_size*(1-target_accuracy))
        num_indices_unmodified = batch_size-num_indices_to_modify
        indices_to_modify = self.rso.choice(range(batch_size), num_indices_to_modify, replace=False)

        for ii in indices_to_modify:
            true_output[ii] += 1

        # convert datatypes to what is expected during operation
        network_output_pt = torch.tensor(fake_network_output, dtype=torch.float)
        true_output_pt = torch.tensor(true_output, dtype=torch.long)

        # now compute the accuracy
        n_total_prev = 64
        n_correct_prev = 50
        expected_accuracy = (num_indices_unmodified+n_correct_prev)/(batch_size+n_total_prev) * 100
        expected_n_total = n_total_prev+batch_size
        expected_n_correct = n_correct_prev + num_indices_unmodified

        actual_acc, n_total, n_correct = \
            _eval_acc(network_output_pt, true_output_pt, n_total=n_total_prev, n_correct=n_correct_prev)
        self.assertAlmostEqual(actual_acc, expected_accuracy)
        self.assertEqual(expected_n_total, n_total)
        self.assertEqual(expected_n_correct, n_correct)

    def test_train_val_split(self):
        t1 = torch.Tensor(np.arange(10))
        dataset = torch.utils.data.TensorDataset(t1)
        split_amt = 0.2
        train_dataset, val_dataset = train_val_dataset_split(dataset, split_amt)
        self.assertEqual(len(train_dataset), int(len(t1)*(1-split_amt)))
        self.assertEqual(len(val_dataset), int(len(t1)*split_amt))

    def test_train_val_split2(self):
        t1 = torch.Tensor(np.arange(10))
        dataset = torch.utils.data.TensorDataset(t1)
        split_amt = 0.0
        train_dataset, val_dataset = train_val_dataset_split(dataset, split_amt)
        self.assertEqual(len(train_dataset), int(len(t1)*(1-split_amt)))
        self.assertEqual(len(val_dataset), int(len(t1)*split_amt))

    def test_str(self):
        training_cfg = TrainingConfig(device='cpu')
        cfg = DefaultOptimizerConfig(training_cfg)
        optimizer_obj = DefaultOptimizer(cfg)
        optimizer_string = str(optimizer_obj)
        correct_string = "{'batch_size':32, 'num_epochs':10, " \
                         "'device':'cpu', 'lr':1.00000e-04, 'loss_function':'cross_entropy_loss', 'optimizer':'adam'}"
        self.assertEqual(optimizer_string, correct_string)


if __name__ == '__main__':
    unittest.main()