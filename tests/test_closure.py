import logging
import unittest
from eudoxa import (
    VDiff, EudoxaManager,
    get_vdiff_relation, set_vdiff_relation,
    TRUE, FALSE, UNDEFINED,
    GT, GTE, DEQ, LTE, LT,
)

logging.getLogger("eudoxa").setLevel(logging.WARNING)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mgr(aspects):
    """
    Build a manager from a dict {aspect_name: [level, ...]}.
    Aspects and levels are added in dict-insertion order.
    """
    mgr = EudoxaManager()
    for name, levels in aspects.items():
        mgr.add_aspect(name, "str")
        for level in levels:
            mgr.add_aspect_level(name, level, None)
    return mgr


def rel(closure, a1, l1a, l1b, a2, l2a, l2b):
    """Return the relation at (Δ(a1,l1a,l1b), Δ(a2,l2a,l2b)) in closure."""
    return get_vdiff_relation(closure, VDiff(a1, l1a, l1b), VDiff(a2, l2a, l2b))


# ── Basic / sanity ────────────────────────────────────────────────────────────

class TestClosureBasic(unittest.TestCase):
    """Sanity checks: empty/minimal setups and reflexivity of zero-diffs."""

    def test_empty_manager_no_collision(self):
        mgr = EudoxaManager()
        _, _, colls = mgr.closure()
        self.assertEqual(colls, [])

    def test_single_aspect_no_relations_no_collision(self):
        mgr = make_mgr({"A": ["1", "2", "3"]})
        _, _, colls = mgr.closure()
        self.assertEqual(colls, [])

    def test_zero_diff_reflexive_intra_aspect(self):
        """◬_A ⊒ ◬_A is pre-established and survives closure."""
        mgr = make_mgr({"A": ["1", "2"]})
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "1", "A", "1", "1"), TRUE)

    def test_zero_diffs_equal_cross_aspect(self):
        """◬_A ⊒ ◬_B and ◬_B ⊒ ◬_A are pre-established."""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"]})
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "1", "B", "1", "1"), TRUE)
        self.assertEqual(rel(closure, "B", "1", "1", "A", "1", "1"), TRUE)

    def test_single_relation_no_collision(self):
        """Setting one GTE relation produces no collision."""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", GTE)
        _, _, colls = mgr.closure()
        self.assertEqual(colls, [])

    def test_unrelated_vdiffs_remain_undefined(self):
        """Setting Δ(A,1,2) ⊒ Δ(B,1,2) should not affect Δ(A,1,2) vs Δ(C,1,2)."""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"], "C": ["1", "2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "C", "1", "2"), UNDEFINED)
        self.assertEqual(rel(closure, "C", "1", "2", "A", "1", "2"), UNDEFINED)


# ── TransP ────────────────────────────────────────────────────────────────────

class TestClosureTransP(unittest.TestCase):
    """TransP: ab⊒cd & cd⊒ef ==> ab⊒ef"""

    def test_transp_intra_aspect(self):
        """Δ(A,1,2)⊒Δ(A,2,3) & Δ(A,2,3)⊒Δ(A,3,4) ==> Δ(A,1,2)⊒Δ(A,3,4)"""
        mgr = make_mgr({"A": ["1", "2", "3", "4"]})
        mgr.set_rel("A", "1", "2", "A", "2", "3", GTE)
        mgr.set_rel("A", "2", "3", "A", "3", "4", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "A", "3", "4"), TRUE)

    def test_transp_cross_aspect(self):
        """Δ(A,1,2)⊒Δ(B,1,2) & Δ(B,1,2)⊒Δ(C,1,2) ==> Δ(A,1,2)⊒Δ(C,1,2)"""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"], "C": ["1", "2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", GTE)
        mgr.set_rel("B", "1", "2", "C", "1", "2", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "C", "1", "2"), TRUE)

    def test_transp_chain_length_4(self):
        """Four-link chain across five aspects derives the end-to-end relation."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"], "C": ["1","2"],
                        "D": ["1","2"], "E": ["1","2"]})
        for a1, a2 in [("A","B"), ("B","C"), ("C","D"), ("D","E")]:
            mgr.set_rel(a1, "1", "2", a2, "1", "2", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "E", "1", "2"), TRUE)

    def test_transp_no_spurious_reverse(self):
        """Δ(A,1,2)⊒Δ(B,1,2) alone must not derive Δ(B,1,2)⊒Δ(A,1,2)."""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "B", "1", "2", "A", "1", "2"), UNDEFINED)


# ── NegTransP ─────────────────────────────────────────────────────────────────

class TestClosureNegTransP(unittest.TestCase):
    """NegTransP: ab⋣cd & cd⋣ef ==> ab⋣ef"""

    def test_negtransp_cross_aspect(self):
        """Δ(A,1,2)⋣Δ(B,1,2) & Δ(B,1,2)⋣Δ(C,1,2) ==> Δ(A,1,2)⋣Δ(C,1,2)"""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"], "C": ["1","2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", LT)
        mgr.set_rel("B", "1", "2", "C", "1", "2", LT)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "C", "1", "2"), FALSE)

    def test_negtransp_chain_length_4(self):
        """Four-link negative chain derives the end-to-end relation."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"], "C": ["1","2"],
                        "D": ["1","2"], "E": ["1","2"]})
        for a1, a2 in [("A","B"), ("B","C"), ("C","D"), ("D","E")]:
            mgr.set_rel(a1, "1", "2", a2, "1", "2", LT)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "E", "1", "2"), FALSE)

    def test_negtransp_no_spurious_positive(self):
        """A single ⋣ assertion must not cause NegTransP to produce FALSE for
        the reverse pair.  set_vdiff_relation is used directly so that the
        complementary ⊒ half is NOT written; the reverse cell must then stay
        UNDEFINED after closure (NegTransP needs two FALSE premises)."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"]})
        mgr.set_vdiff_relation(VDiff("A","1","2"), VDiff("B","1","2"), FALSE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        # No rule can derive Δ(B,1,2)⋣Δ(A,1,2) from a single premise
        self.assertEqual(rel(closure, "B", "1", "2", "A", "1", "2"), UNDEFINED)


# ── DiffP / NegDiffP ──────────────────────────────────────────────────────────

class TestClosureDiffP(unittest.TestCase):
    """DiffP:    cd⊒ef (same aspect) ==> ce⊒df
       NegDiffP: cd⋣ef (same aspect) ==> fd⋣ec"""

    def test_diffp(self):
        """Δ(A,1,3)⊒Δ(A,2,4) ==> Δ(A,1,2)⊒Δ(A,3,4)
           (c=1,d=3,e=2,f=4 → ce=Δ(1,2), df=Δ(3,4))"""
        mgr = make_mgr({"A": ["1", "2", "3", "4"]})
        mgr.set_rel("A", "1", "3", "A", "2", "4", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "A", "3", "4"), TRUE)

    def test_negdiffp(self):
        """Δ(A,1,3)⋣Δ(A,2,4) ==> Δ(A,4,3)⋣Δ(A,2,1)
           (c=1,d=3,e=2,f=4 → fd=Δ(4,3), ec=Δ(2,1))"""
        mgr = make_mgr({"A": ["1", "2", "3", "4"]})
        mgr.set_rel("A", "1", "3", "A", "2", "4", LT)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "4", "3", "A", "2", "1"), FALSE)

    def test_diffp_does_not_apply_cross_aspect(self):
        """DiffP is only for same-aspect pairs; cross-aspect GTE should not trigger it."""
        mgr = make_mgr({"A": ["1", "2", "3", "4"], "B": ["1", "2", "3", "4"]})
        mgr.set_rel("A", "1", "3", "B", "2", "4", GTE)  # cross-aspect: no DiffP
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        # Δ(A,1,2)⊒Δ(B,3,4) must NOT be derived (DiffP only applies within one aspect)
        self.assertEqual(rel(closure, "A", "1", "2", "B", "3", "4"), UNDEFINED)

    def test_diffp_then_transp(self):
        """DiffP creates a new intermediate; TransP then chains through it.
           Δ(A,1,3)⊒Δ(A,2,4) → DiffP → Δ(A,1,2)⊒Δ(A,3,4)
           Δ(A,3,4)⊒Δ(B,1,2)  → TransP → Δ(A,1,2)⊒Δ(B,1,2)
           This may require the outer fixed-point pass to complete."""
        mgr = make_mgr({"A": ["1", "2", "3", "4"], "B": ["1", "2"]})
        mgr.set_rel("A", "1", "3", "A", "2", "4", GTE)
        mgr.set_rel("A", "3", "4", "B", "1", "2", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "B", "1", "2"), TRUE)


# ── InvP_R / InvP_L ───────────────────────────────────────────────────────────

class TestClosureInvP(unittest.TestCase):
    """InvP_R: ab⊒cd & cd⊒xx ==> dc⊒ba
       InvP_L: xx⊒cd & cd⊒ef ==> fe⊒dc"""

    def test_invp_r(self):
        """Δ(A,1,2)⊒Δ(B,1,2) & Δ(B,1,2)⊒◬_B ==> Δ(B,2,1)⊒Δ(A,2,1)"""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", GTE)
        # Δ(B,1,2) ⊒ ◬_B  (use same-level for zero-diff)
        mgr.set_rel("B", "1", "2", "B", "1", "1", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        # dc=Δ(B,2,1), ba=Δ(A,2,1)
        self.assertEqual(rel(closure, "B", "2", "1", "A", "2", "1"), TRUE)

    def test_invp_l(self):
        """◬_A⊒Δ(A,2,1) & Δ(A,2,1)⊒Δ(B,2,1) ==> Δ(B,1,2)⊒Δ(A,1,2)"""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"]})
        # ◬_A ⊒ Δ(A,2,1): zero-diff ≥ Δ(A,2,1), i.e. Δ(A,2,1) is non-positive
        mgr.set_rel("A", "1", "1", "A", "2", "1", GTE)
        mgr.set_rel("A", "2", "1", "B", "2", "1", GTE)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        # fe=Δ(B,1,2), dc=Δ(A,1,2)
        self.assertEqual(rel(closure, "B", "1", "2", "A", "1", "2"), TRUE)


# ── NegInvP_L / NegInvP_R ────────────────────────────────────────────────────

class TestClosureNegInvP(unittest.TestCase):
    """NegInvP_L: xx⋣cd & cd⋣ef ==> fe⋣dc
       NegInvP_R: ab⋣cd & cd⋣xx ==> dc⋣ba"""

    def test_neginvp_l(self):
        """◬_A⋣Δ(A,1,2) & Δ(A,1,2)⋣Δ(B,1,2) ==> Δ(B,2,1)⋣Δ(A,2,1)"""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"]})
        # ◬_A ⋣ Δ(A,1,2): GT sets Δ(A,1,2)⊒◬_A and ◬_A⋣Δ(A,1,2)
        mgr.set_rel("A", "1", "2", "A", "1", "1", GT)
        # Δ(A,1,2) ⋣ Δ(B,1,2): LT sets Δ(B,1,2)⊒Δ(A,1,2) and Δ(A,1,2)⋣Δ(B,1,2)
        mgr.set_rel("A", "1", "2", "B", "1", "2", LT)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        # fe=Δ(B,2,1), dc=Δ(A,2,1)
        self.assertEqual(rel(closure, "B", "2", "1", "A", "2", "1"), FALSE)

    def test_neginvp_r(self):
        """Δ(A,2,1)⋣Δ(B,2,1) & Δ(B,2,1)⋣◬_B ==> Δ(B,1,2)⋣Δ(A,1,2)"""
        mgr = make_mgr({"A": ["1", "2"], "B": ["1", "2"]})
        mgr.set_rel("A", "2", "1", "B", "2", "1", LT)
        # Δ(B,2,1) ⋣ ◬_B: LT sets ◬_B⊒Δ(B,2,1) and Δ(B,2,1)⋣◬_B
        mgr.set_rel("B", "2", "1", "B", "1", "1", LT)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        # dc=Δ(B,1,2), ba=Δ(A,1,2)
        self.assertEqual(rel(closure, "B", "1", "2", "A", "1", "2"), FALSE)


# ── NegTransP_DEQ_L / NegTransP_DEQ_R ────────────────────────────────────────

class TestClosureNegTransPDEQ(unittest.TestCase):
    """NegTransP_DEQ_L: ab≜cd & cd⋣ef ==> ab⋣ef
       NegTransP_DEQ_R: ab⋣cd & cd≜ef ==> ab⋣ef"""

    def test_negtransp_deq_l(self):
        """Δ(A,1,2)≜Δ(B,1,2) & Δ(B,1,2)⋣Δ(C,1,2) ==> Δ(A,1,2)⋣Δ(C,1,2)"""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"], "C": ["1","2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", DEQ)
        mgr.set_rel("B", "1", "2", "C", "1", "2", LT)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "C", "1", "2"), FALSE)

    def test_negtransp_deq_r(self):
        """Δ(A,1,2)⋣Δ(B,1,2) & Δ(B,1,2)≜Δ(C,1,2) ==> Δ(A,1,2)⋣Δ(C,1,2)"""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"], "C": ["1","2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", LT)
        mgr.set_rel("B", "1", "2", "C", "1", "2", DEQ)
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        self.assertEqual(rel(closure, "A", "1", "2", "C", "1", "2"), FALSE)

    def test_negtransp_deq_l_not_spurious(self):
        """DEQ alone (without a ⋣ premise) must not produce a ⋣ conclusion."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"], "C": ["1","2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", DEQ)
        mgr.set_rel("B", "1", "2", "C", "1", "2", GTE)   # ⊒, not ⋣
        closure, _, colls = mgr.closure()
        self.assertEqual(colls, [])
        # Only TransP should fire: Δ(A,1,2)⊒Δ(C,1,2)
        self.assertEqual(rel(closure, "A", "1", "2", "C", "1", "2"), TRUE)
        # No ⋣ in this direction
        self.assertNotEqual(rel(closure, "A", "1", "2", "C", "1", "2"), FALSE)


# ── Collision detection ───────────────────────────────────────────────────────

class TestClosureCollisions(unittest.TestCase):

    def test_set_vdiff_relation_detects_direct_collision(self):
        """set_vdiff_relation itself detects TRUE/FALSE clashes immediately.
        GT sets (A12,B12)=TRUE and (B12,A12)=FALSE; trying to then set
        (B12,A12)=TRUE must return a non-None collision tuple."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", GT)
        _, coll = mgr.set_vdiff_relation(VDiff("B","1","2"), VDiff("A","1","2"), TRUE)
        self.assertIsNotNone(coll)

    def test_collision_via_transp(self):
        """TransP derives Δ(A,1,2)⊒Δ(C,1,2); asserting ⋣ at that cell collides."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"], "C": ["1","2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", GTE)
        mgr.set_rel("B", "1", "2", "C", "1", "2", GTE)
        mgr.set_vdiff_relation(VDiff("A","1","2"), VDiff("C","1","2"), FALSE)
        _, _, colls = mgr.closure()
        self.assertGreater(len(colls), 0)

    def test_collision_via_negtransp(self):
        """NegTransP derives Δ(A,1,2)⋣Δ(C,1,2); asserting ⊒ at that cell collides."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"], "C": ["1","2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", LT)
        mgr.set_rel("B", "1", "2", "C", "1", "2", LT)
        mgr.set_vdiff_relation(VDiff("A","1","2"), VDiff("C","1","2"), TRUE)
        _, _, colls = mgr.closure()
        self.assertGreater(len(colls), 0)

    def test_collision_via_diffp(self):
        """DiffP derives Δ(A,1,2)⊒Δ(A,3,4); asserting ⋣ at that cell collides."""
        mgr = make_mgr({"A": ["1","2","3","4"]})
        mgr.set_rel("A", "1", "3", "A", "2", "4", GTE)
        mgr.set_vdiff_relation(VDiff("A","1","2"), VDiff("A","3","4"), FALSE)
        _, _, colls = mgr.closure()
        self.assertGreater(len(colls), 0)

    def test_collision_via_negdiffp(self):
        """NegDiffP derives Δ(A,4,3)⋣Δ(A,2,1); asserting ⊒ at that cell collides."""
        mgr = make_mgr({"A": ["1","2","3","4"]})
        mgr.set_rel("A", "1", "3", "A", "2", "4", LT)
        mgr.set_vdiff_relation(VDiff("A","4","3"), VDiff("A","2","1"), TRUE)
        _, _, colls = mgr.closure()
        self.assertGreater(len(colls), 0)

    def test_collision_via_invp_r(self):
        """InvP_R derives Δ(B,2,1)⊒Δ(A,2,1); asserting ⋣ at that cell collides."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"]})
        mgr.set_rel("A", "1", "2", "B", "1", "2", GTE)
        mgr.set_rel("B", "1", "2", "B", "1", "1", GTE)  # Δ(B,1,2) ⊒ ◬_B
        mgr.set_vdiff_relation(VDiff("B","2","1"), VDiff("A","2","1"), FALSE)
        _, _, colls = mgr.closure()
        self.assertGreater(len(colls), 0)

    def test_collision_via_invp_l(self):
        """InvP_L derives Δ(B,1,2)⊒Δ(A,1,2); asserting ⋣ at that cell collides."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"]})
        mgr.set_rel("A", "1", "1", "A", "2", "1", GTE)  # ◬_A ⊒ Δ(A,2,1)
        mgr.set_rel("A", "2", "1", "B", "2", "1", GTE)
        mgr.set_vdiff_relation(VDiff("B","1","2"), VDiff("A","1","2"), FALSE)
        _, _, colls = mgr.closure()
        self.assertGreater(len(colls), 0)

    def test_collision_via_neginvp_l(self):
        """NegInvP_L derives Δ(B,2,1)⋣Δ(A,2,1); asserting ⊒ at that cell collides."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"]})
        mgr.set_rel("A", "1", "2", "A", "1", "1", GT)   # ◬_A ⋣ Δ(A,1,2)
        mgr.set_rel("A", "1", "2", "B", "1", "2", LT)   # Δ(A,1,2) ⋣ Δ(B,1,2)
        mgr.set_vdiff_relation(VDiff("B","2","1"), VDiff("A","2","1"), TRUE)
        _, _, colls = mgr.closure()
        self.assertGreater(len(colls), 0)

    def test_collision_via_neginvp_r(self):
        """NegInvP_R derives Δ(B,1,2)⋣Δ(A,1,2); asserting ⊒ at that cell collides."""
        mgr = make_mgr({"A": ["1","2"], "B": ["1","2"]})
        mgr.set_rel("A", "2", "1", "B", "2", "1", LT)
        mgr.set_rel("B", "2", "1", "B", "1", "1", LT)   # Δ(B,2,1) ⋣ ◬_B
        mgr.set_vdiff_relation(VDiff("B","1","2"), VDiff("A","1","2"), TRUE)
        _, _, colls = mgr.closure()
        self.assertGreater(len(colls), 0)

    def test_consistent_structure_no_collision(self):
        """A well-formed set of consistent relations must produce no collision."""
        mgr = make_mgr({"A": ["1","2","3"], "B": ["1","2"]})
        mgr.set_rel("A", "1", "3", "A", "1", "2", GT)   # Δ(A,1,3) ⊐ Δ(A,1,2)
        mgr.set_rel("A", "1", "2", "B", "1", "2", GT)   # Δ(A,1,2) ⊐ Δ(B,1,2)
        mgr.set_rel("B", "1", "2", "A", "2", "3", GTE)  # Δ(B,1,2) ⊒ Δ(A,2,3)
        _, _, colls = mgr.closure()
        self.assertEqual(colls, [])


if __name__ == "__main__":
    unittest.main()
