from django.shortcuts import render

def swimming_lane_diagram(request):
    """
    View for displaying the swimming lane diagram.
    """
    return render(request, 'users/diagram.html')
