"""Explainable AI Financial Fraud and Risk Detection Backend Application."""
import sys
import types

__version__ = "2.0.1"

# Prevent Windows Application Control DLL load failure for hist_gradient_boosting histogram extension
try:
    from sklearn.ensemble._hist_gradient_boosting.histogram import HistogramBuilder
except Exception:
    m_hist = types.ModuleType("sklearn.ensemble._hist_gradient_boosting.histogram")
    m_hist.HistogramBuilder = object
    sys.modules["sklearn.ensemble._hist_gradient_boosting.histogram"] = m_hist

    try:
        from sklearn.ensemble._hist_gradient_boosting.grower import TreeGrower
    except Exception:
        m_grow = types.ModuleType("sklearn.ensemble._hist_gradient_boosting.grower")
        m_grow.TreeGrower = object
        sys.modules["sklearn.ensemble._hist_gradient_boosting.grower"] = m_grow
