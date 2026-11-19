"""Pure grading logic. Scores and correct answers never come from the client."""
def grade(questions, answers):
    if not isinstance(answers, list) or not questions or len(answers) != len(questions):
        raise ValueError('Answer every question before submitting.')
    if any(answer not in ('a', 'b', 'c', 'd') for answer in answers):
        raise ValueError('Choose a valid answer for every question.')
    correct = sum(answer == question['correct_answer'] for answer, question in zip(answers, questions))
    return correct, round(100 * correct / len(questions))
