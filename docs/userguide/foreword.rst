Foreword
========

Motivation
----------

It was a nice day in the summer of 2014, when the professor contacted me.  She asked me whether there was some online judging websites that could train software enginneering skills.

Software enginneering is a special course among all programming courses.  The skills, such as testing, code styles, deploying, are all difficult to evaluate.  Most online judging systems only care about the output of program, not the behaviour of the program.

We need a new online judger!  Then Railgun was born.

.. _requirement:

Requirements
------------

What should Railgun be?  It's a pretty hard question, but let me first mention some classical problems in software enginneering:

.. tabularcolumns:: |p{4cm}|p{11cm}|

=================== =========================================================
Problem             Way of Evaluation
=================== =========================================================
Coding Style        How "pretty" the code is.
Unit Testing        The unit test should be "complete", and the code should
                    be organized neatly.
WhiteBox Testing    In addition to the base demands of unit test, it should
                    cover as much code as possible.
BlackBox Testing    How many input classes and boundary values can the
                    student cover?
Deployment          The only mission is to let a given software run.
=================== =========================================================

How complicated the ways of evaluation!  There just does not exist a simple way, like comparing the program output with a "correct" answer, to give out the score.

.. _philosophy:

Philosophy
----------

If we could not pick out the common behaviour, we just leave it alone.  The way to deal with such a lot of different evaluation standards, is to let the assignment itself evaluate the student submissions.

For example, an assignment of Python coding style can simply run "pep8" script to evaluate a given submission.  Other types of assignments, like unit testing and whitebox testing, may run particular tools to get coverage statistics.

Even the evaluation of a deployment assigment is very simple: we may let the students to deploy a given program on a public accessible server, and use our unit tests to check the behaviour of the remote server.

This is the philosophy of Railgun system: it only stores and puts them into the run queue, waits for evaluations finishing in external processes, and receives the final scores.  For more details about the system, you may refer to :ref:`design`.
