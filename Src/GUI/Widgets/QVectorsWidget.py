import os

import wx

from MDANSE import REGISTRY

from MDANSE.GUI.Widgets.UserDefinitionWidget import UserDefinitionDialog, UserDefinitionWidget
        
class QVectorsWidget(UserDefinitionWidget):
    
    pass
        
REGISTRY["q_vectors"] = QVectorsWidget
        
if __name__ == "__main__":
    
    from MMTK.Trajectory import Trajectory
    
    from MDANSE import PLATFORM
    
    t = Trajectory(None,os.path.join(PLATFORM.example_data_directory(),"Trajectories","MMTK","protein_in_periodic_universe.nc"),"r")
    
    app = wx.App(False)
    
    p = UserDefinitionDialog(None,t,'q_vectors')
        
    p.SetSize((800,800))
            
    p.ShowModal()
    
    p.Destroy()
    
    app.MainLoop()
        
