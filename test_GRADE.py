import unittest
import GRADE
from detect_cants_and_knots import Box


class GradeTestCase(unittest.TestCase):
    """Tests for 'GRADE.py'."""

    def test_determine_how_many_boards(self):
        """Is a 6" faced 2x6 cant sucessfully GRADE.determined to have 3 boards?
        """
        self.assertEqual(GRADE.determine_how_many_boards(0.125, 1.7, 6), 3)

    def test_find_longest_good_section_1(self):
        self.assertEqual(GRADE.find_longest_good_section([True,
                                                          False,
                                                          True,
                                                          True,
                                                          True,
                                                          False]), 3)

    def test_find_longest_good_section_2(self):
        self.assertEqual(GRADE.find_longest_good_section([True,
                                                          False,
                                                          True,
                                                          False,
                                                          True,
                                                          False]), 1)

    def test_find_longest_good_section_3(self):
        self.assertEqual(GRADE.find_longest_good_section([False,
                                                          False,
                                                          False,
                                                          False,
                                                          False,
                                                          False]), 0)

    def test_find_longest_good_section_4(self):
        self.assertEqual(GRADE.find_longest_good_section([True,
                                                          True,
                                                          True,
                                                          True,
                                                          True,
                                                          True]), 6)

    def test_clip_knots_to_cant_face1(self):
        cants = [Box(5, 5, 25, 25, 1)]
        knots = [Box(1, 7, 10, 10, 1)]
        n_knots = GRADE.clip_knots_to_cant_face(cants, knots)
        self.assertNotEqual(knots, n_knots)

    def test_clip_knots_to_cant_face2(self):
        cants = [Box(5, 5, 25, 25, 1)]
        knots = [Box(1, 7, 10, 10, 1)]
        n_knots = GRADE.clip_knots_to_cant_face(cants, knots)
        test_box = Box(5, 7, 10, 10, 1)
        for knot in n_knots:
            self.assertEqual(knot.ymin, test_box.ymin)
            self.assertEqual(knot.xmin, test_box.xmin)
            self.assertEqual(knot.ymax, test_box.ymax)
            self.assertEqual(knot.xmax, test_box.xmax)

    def test_clip_knots_to_cant_face3(self):
        cants = [Box(5, 5, 25, 25, 1)]
        knots = [Box(1, 7, 10, 10, 1)]
        n_knots = GRADE.clip_knots_to_cant_face(cants, knots)
        self.assertFalse(n_knots is knots)


if __name__ == '__main__':
    unittest.main()
