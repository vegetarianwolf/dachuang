from csmarapi.CsmarService import CsmarService
from csmarapi.ReportUtil import ReportUtil

def main():
    print("Hello from dachuang!")
    
    # 1. 初始化 CSMAR 服务
    csmar = CsmarService()
    print("CSMAR 服务初始化成功")
    csmar.login('2412782@mail.nankai.edu.cn','21288480Yy')
    # 2. 如果需要以表格形式展示数据，可配合 ReportUtil 使用
    #例：      
    database = csmar.getListDbs()      
    ReportUtil(database)
if __name__ == "__main__":
    main()
