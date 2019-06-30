import unittest

import numpy as np

from prml import autodiff


class TestGaussian(unittest.TestCase):

    def test_gaussian(self):
        samples = autodiff.random.gaussian(-2.3, 0.5, size=100000).value
        self.assertAlmostEqual(-2.3, np.mean(samples), places=2)
        self.assertAlmostEqual(0.5, np.std(samples), places=2)

    def test_multivariate_gaussian(self):
        expect_mean = np.array([1, -1.5])
        expect_covariance = np.array([[0.2, 0.1], [0.1, 0.2]])
        samples = autodiff.random.multivariate_gaussian(
            expect_mean, expect_covariance, size=(100000, 2)).value
        actual_mean = np.mean(samples, axis=0)
        actual_covariance = np.cov(samples, rowvar=False)
        self.assertTrue(
            np.allclose(expect_mean, actual_mean, atol=1e-2),
            msg=f"{expect_mean}\n{actual_mean}")
        self.assertTrue(
            np.allclose(expect_covariance, actual_covariance, atol=1e-2),
            msg=f"{expect_covariance}\n{actual_covariance}")

    def test_gaussian_logpdf(self):
        x = 2
        mean = 1
        std = 1
        expect = -0.5 * ((x - mean) / std) ** 2 - 0.5 * np.log(2 * np.pi) - np.log(std)
        actual = autodiff.random.gaussian_logpdf(x, mean, std).value[0]
        self.assertAlmostEqual(expect, actual)

        mean = autodiff.zeros(1)
        std = autodiff.ones(1)
        x = np.random.normal(1.5, 2, size=10000)
        for _ in range(1000):
            mean.cleargrad()
            std.cleargrad()
            loglikelihood = autodiff.random.gaussian_logpdf(x, mean, std)
            loglikelihood = loglikelihood.mean()
            loglikelihood.backprop()
            mean.value += 0.1 * mean.grad
            std.value += 0.1 * std.grad
        self.assertAlmostEqual(x.mean(), mean.value[0], places=2)
        self.assertAlmostEqual(x.std(), std.value[0], places=2)

    def test_bayesnet(self):
        qmu_m = autodiff.zeros(1)
        qmu_s = autodiff.array([np.log(0.1)])
        history_log = {"elbo": [], "mean": [], "std": []}
        for _ in range(10000):
            qmu_std = autodiff.exp(qmu_s)
            mu = autodiff.random.gaussian(qmu_m, qmu_std)
            elbo = (
                autodiff.random.gaussian_logpdf([0.8], mu, 0.1).sum()
                + autodiff.random.gaussian_logpdf(mu, 0, 0.1)
                - autodiff.random.gaussian_logpdf(mu, qmu_m, qmu_std)
            )
            history_log["elbo"].append(elbo.value[0])
            history_log["mean"].append(qmu_m.value[0])
            history_log["std"].append(qmu_std.value[0])
            autodiff.backprop(elbo)
            qmu_m.value += 1e-3 * qmu_m.grad
            qmu_s.value += 1e-3 * qmu_s.grad
        self.assertAlmostEqual(0.4, qmu_m.value[0], places=1)
        self.assertAlmostEqual(np.sqrt(0.005), qmu_std.value[0], places=1)


if __name__ == "__main__":
    unittest.main()
