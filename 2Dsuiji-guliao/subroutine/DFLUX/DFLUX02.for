      SUBROUTINE DFLUX(FLUX,SOL,KSTEP,KINC,TIME,NOEL,NPT,COORDS,
     1 JLTYP,TEMP,PRESS,SNAME)
C
      INCLUDE 'ABA_PARAM.INC'
C
      DIMENSION FLUX(2), TIME(2), COORDS(3)
      CHARACTER*80 SNAME
C      user coding to define FLUX(1) and FLUX(2)
C     ��˹����Դģ��   
C     ��Դ����
      real velocity
      real center_x,center_z
      real P,p1,pi,r0,h,r

C     �����ٶ�
      velocity = 1.2
      
C     ��Դ���ĵ�����,������Դ�������ƶ��ģ�����zֵ���ں����ٶ�*��ʱ��
      center_x = 35.0
      center_z = time(2)*velocity
      
C     ������ȡ�ĸ�˹��Դ����     
      P = 2400
      p1 = 0.1
      pi = 3.14
      r0 = 4

C     �ڵ������Դ���ĵľ���
      r = sqrt((coords(1)-center_x)**2+(coords(3)-center_z)**2)
      
      Flux(1) = 3*P*p1*exp(-(3*r**2)/r0**2)/(pi*r0**2)


      RETURN
      END
      
      
      
      
      
      